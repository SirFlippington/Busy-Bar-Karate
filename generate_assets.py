"""Rebuild every Karate asset from original geometric pixel drawings and synthesized audio.
No external images, recordings, sprite sheets, or melodies are read.
Requires Pillow and NumPy. Output is deterministic.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
import numpy as np
import struct, math, shutil
root=Path(__file__).resolve().parent
for folder in ['images','animations','sounds']:
    shutil.rmtree(root/folder,ignore_errors=True)
    (root/folder).mkdir()
animation_dir=root/'animations'
colors={'master':('#35C7FF','#F2FBFF'),'grabber':('#F05DC4','#FFB9E9'),'brute':('#E89B35','#FFF097'),'striker':('#7276CD','#D0D4FF'),'boss':('#5FDA9D','#FFF29D')}
poses=['idle','walk1','walk2','walk3','punch','kick','grab','hurt','down','leap']
def original(actor,pose):
    # Compact, broad-shouldered figures drawn specifically at LED pixel resolution.
    w,h=(24,14) if actor=='boss' else (20,14 if actor=='master' else 12)
    im=Image.new('RGBA',(w,h));d=ImageDraw.Draw(im);cx=w//2;top=h-12
    main,light=colors[actor];skin='#FFD1A3';ink='#12243B';feet='#DBECFF'
    lean=-1 if pose in ('hurt','down') else 0
    cx+=lean
    # Four distinct grounded steps, feet always share the floor baseline.
    legs={'walk1':(-3,2),'walk2':(-1,1),'walk3':(-2,3)}.get(pose,(-2,2))
    d.line([(cx-1,top+7),(cx+legs[0],h-2)],fill=main,width=2)
    d.line([(cx+1,top+7),(cx+legs[1],h-2)],fill=light,width=2)
    d.line([(cx+legs[0]-1,h-1),(cx+legs[0]+1,h-1)],fill=feet)
    d.line([(cx+legs[1],h-1),(cx+legs[1]+2,h-1)],fill=feet)
    if pose=='kick':
        d.rectangle((cx,top+8,cx+4,h-1),fill=(0,0,0,0))
        d.line([(cx,top+7),(cx+4,top+6),(cx+7,top+6)],fill=light,width=2)
        d.point((cx+8,top+6),fill=feet)
    if pose=='leap':
        d.rectangle((cx-5,top+8,cx+5,h-1),fill=(0,0,0,0))
        d.line([(cx,top+7),(cx-3,top+9),(cx-1,top+10)],fill=main,width=2)
        d.line([(cx+1,top+7),(cx+4,top+8),(cx+3,top+10)],fill=light,width=2)
    broad=3 if actor in ('brute','boss') else 2
    d.rectangle((cx-broad,top+4,cx+2,top+7),fill=main)
    d.line((cx-2,top+7,cx+2,top+7),fill=ink)
    d.line((cx+1,top+4,cx,top+6),fill=light)
    # Squared head with a clear forward-facing nose and dark headband.
    d.rectangle((cx-1,top,cx+2,top+3),fill=skin)
    d.line((cx-1,top,cx+2,top),fill=ink)
    d.point((cx+3,top+2),fill=skin);d.point((cx+2,top+1),fill=ink)
    if actor=='master':d.line((cx-3,top+1,cx+1,top+1),fill='#F5F7FF')
    if actor=='boss':d.line((cx-2,top,cx+2,top),fill='#FFE066')
    # Guard, wind-up and full extension are separate authored silhouettes.
    end= (cx+7,top+4) if pose=='punch' else (cx+4,top+3)
    if pose=='grab':end=(cx+5,top+5)
    if pose in ('hurt','down'):end=(cx-4,top+2)
    d.line([(cx+1,top+4),end],fill=light,width=2);d.point(end,fill=skin)
    d.line([(cx-2,top+4),(cx-3,top+6),(cx-1,top+6)],fill=main,width=2)
    if pose=='down':im=im.rotate(-55,resample=Image.Resampling.NEAREST)
    return im
images={}
for actor in colors:
    for pose in poses:
        base=original(actor,pose)
        for display in ['front','back']:
            img=base if display=='front' else base.resize((48,32),Image.Resampling.NEAREST)
            for direction in ['r','l']:
                frame=img if direction=='r' else ImageOps.mirror(img)
                images[actor,pose,direction,display]=frame
                frame.save(root/'images'/f'{actor}_{pose}_{direction}_{display}.png')

def compress(frame):
    # Minimal lossless QOI stream: explicit RGBA pixels plus runs of identical pixels.
    pixels=frame.tobytes();out=bytearray();last=None;run=0
    for i in range(0,len(pixels),4):
        px=pixels[i:i+4]
        if px==last and run<62:run+=1;continue
        if run:out.append(0xc0+run-1);run=0
        if px==last:run=1
        else:out.append(0xff);out.extend(px);last=px
    if run:out.append(0xc0+run-1)
    return bytes(out)

def encode(path,frames,sections,fps=30):
    width,height=frames[0].size
    encoded=[compress(f) for f in frames]
    chunks=[struct.pack('<BHH',18,0,len(b))+b for b in encoded]
    sections=[('default',0,len(frames)-1)]+sections
    offset=34+sum(13+len(n) for n,_,_ in sections);offsets=[]
    for c in chunks:offsets.append(offset);offset+=len(c)
    secs=b''.join(struct.pack('<III',a,b,offsets[a])+n.encode()+b'\0' for n,a,b in sections)
    header=struct.pack('<8sBBBBHHBBIIII',b'bicycle1',0,width,height,2,0,max(map(len,encoded)),fps,0,len(secs),sum(map(len,chunks)),len(sections),len(chunks))
    path.write_bytes(header+secs+b''.join(chunks))

def actor_frames(actor,direction,display):
    frames=[];sections=[];idle=images[actor,'idle',direction,display]
    for pose in poses:
        body=images[actor,pose,direction,display]
        seq=[body]
        if pose in ('punch','kick'):
            # Ease the limb out and back using a translated silhouette, not a teleport.
            half=Image.new('RGBA',body.size)
            half.alpha_composite(body,(-1 if direction=='r' else 1,0))
            seq=[idle]*2+[half]*2+[body]*4+[half]*2+[idle]*2
        if pose in ('hurt','down'):
            seq=[]
            for i in range(12):
                f=Image.new('RGBA',body.size);f.alpha_composite(body,(0,round((i/11)**2*body.height)));seq.append(f)
        first=len(frames);frames.extend(seq);sections.append((pose,first,len(frames)-1))
    first=len(frames)
    for pose in ['walk1','walk2','walk3','walk2']:frames.extend([images[actor,pose,direction,display]]*3)
    sections.append(('walk',first,len(frames)-1))
    return frames,sections
for actor in colors:
    for direction in ['l','r']:
        for display in ['front','back']:
            frames,sections=actor_frames(actor,direction,display)
            encode(animation_dir/f'{actor}_{direction}_{display}.anim',frames,sections)
frames=[];sections=[]
for direction in ['l','r']:
    fs,ss=actor_frames('master',direction,'front');off=len(frames);frames.extend(fs)
    sections.extend((n+'_'+direction,a+off,b+off) for n,a,b in ss)
encode(animation_dir/'master_front.anim',frames,sections)
speeds = {
    "grabber": [13, 14, 15, 16, 17, 18, 19],
    "brute": [8, 9, 10, 11, 12, 13, 14],
    "striker": [15, 17, 19, 21, 23, 25, 27],
}
stops = {"grabber": 5, "brute": 7, "striker": 5}
motion_meta = {}
for actor, tier_speeds in speeds.items():
    for tier, speed in enumerate(tier_speeds):
        for side, direction in [(-1, "r"), (1, "l")]:
            start = -6 if side < 0 else 78
            stop = 36 + side * stops[actor]
            distance = abs(stop - start)
            count = math.ceil(distance / speed * 30) + 1
            frames = []
            for index in range(count):
                x = start - side * min(distance, speed * index / 30)
                pose = ["walk1", "walk2", "walk3", "walk2"][int(index / 3) % 4]
                frame = Image.new("RGBA", (72, 12))
                frame.alpha_composite(images[(actor, pose, direction, "front")], (round(x) - 10, 0))
                frames.append(frame)
            name = f"approach_{actor}_{direction}_{tier}"
            # Hold arrival while the game sends the combat section. Without this
            # tail, a looping path can briefly wrap back to the edge of the screen.
            frames.extend([frames[-1]] * 30)
            sections = [("enter", 0, len(frames) - 1)]
            body, body_sections = actor_frames(actor, direction, "front")
            offset = len(frames)
            for body_frame in body:
                frame = Image.new("RGBA", (72, 12))
                frame.alpha_composite(body_frame, (round(stop) - 10, 0))
                frames.append(frame)
            sections.extend(
                (section_name, first + offset, last + offset)
                for section_name, first, last in body_sections
            )
            encode(animation_dir / f"{name}.anim", frames, sections)
            motion_meta[name] = (count - 1) / 30

# The boss crosses the entire front display in a native 30 fps arc. The game
# switches direction at the same 1.4-second boundary, so no HTTP frame updates
# are needed during the jump.
boss_frames = []
boss_sections = []
boss_jump_seconds = 1.4
boss_jump_frames = round(boss_jump_seconds * 30)
for direction, start_x, end_x in [("r", 5, 67), ("l", 67, 5)]:
    first = len(boss_frames)
    for index in range(boss_jump_frames):
        progress = index / (boss_jump_frames - 1)
        x = start_x + (end_x - start_x) * progress
        y = 5 - round(5 * math.sin(math.pi * progress))
        pose = "kick" if 0.32 < progress < 0.68 else "leap"
        frame = Image.new("RGBA", (72, 16))
        jumper = images[("boss", pose, direction, "front")].resize((20, 9), Image.Resampling.NEAREST)
        frame.alpha_composite(jumper, (round(x) - 10, y))
        boss_frames.append(frame)
    boss_frames.extend([boss_frames[-1]] * 20)
    boss_sections.append(("jump_" + direction, first, len(boss_frames) - 1))
    first = len(boss_frames)
    for index in range(48):
        progress = index / 47
        distance = 42 * progress if progress < .5 else 42 * (1-progress)
        x = start_x + (distance if direction == 'r' else -distance)
        pose = 'punch' if .38 < progress < .5 else ['walk1','walk2'][int(index/4)%2]
        facing = direction if progress < .5 else ('l' if direction == 'r' else 'r')
        frame = Image.new('RGBA',(72,16))
        frame.alpha_composite(images[('boss',pose,facing,'front')], (round(x)-12,1))
        boss_frames.append(frame)
    boss_frames.extend([boss_frames[-1]] * 20)
    boss_sections.append(('step_'+direction,first,len(boss_frames)-1))
for direction, x in [("r", 5), ("l", 67)]:
    first = len(boss_frames)
    for _ in range(6):
        frame = Image.new("RGBA", (72, 16))
        frame.alpha_composite(images[("boss", "idle", direction, "front")], (x - 12, 2))
        boss_frames.append(frame)
    boss_sections.append(("idle_" + direction, first, len(boss_frames) - 1))
encode(animation_dir / "boss_front.anim", boss_frames, boss_sections)

# A single native clip falls through the floor and finishes on transparency.
# It has its own source file so the normal player timer restarts on a new run.
fall_frames=[]
fall_sections=[]
for direction in ['l','r']:
    body=Image.open(root/'images'/f'master_down_{direction}_front.png').convert('RGBA')
    first=len(fall_frames)
    for index in range(30):
        frame=Image.new('RGBA',(20,16))
        offset=1+round(19*(index/29)**1.7)
        frame.alpha_composite(body,(0,offset))
        fall_frames.append(frame)
    assert not fall_frames[-1].getbbox()
    fall_sections.append(('fall_'+direction,first,len(fall_frames)-1))
encode(animation_dir/'master_fall.anim',fall_frames,fall_sections)


# Original moonlit rooftop arena: navy sky, distant towers, teal floor.
bg=Image.new('RGBA',(72,16),'#0A142B');d=ImageDraw.Draw(bg)
for x,y in [(3,3),(17,2),(40,4),(59,2),(66,5)]:d.point((x,y),fill='#677DA1')
d.ellipse((48,2,52,6),fill='#536D92')
for x,h in [(0,5),(8,3),(20,4),(45,3),(58,5),(68,4)]:d.rectangle((x,13-h,x+5,13),fill='#182A43')
d.line((0,14,71,14),fill='#3B7C88');d.line((0,15,71,15),fill='#183D50')
bg.save(root/'images/front.png')
bg.resize((160,80),Image.Resampling.NEAREST).save(root/'images/back.png')
# Original eight-pixel fist icon for the catalog.
icon=Image.new('RGBA',(8,8),(0,0,0,0));pen=ImageDraw.Draw(icon)
pen.rectangle((1,2,5,5),fill='#35C7FF');pen.rectangle((2,1,6,3),fill='#FFD1A3')
pen.line((2,2,6,2),fill='#F2FBFF');pen.rectangle((0,5,3,6),fill='#35C7FF')
icon.save(root/'appmeta/icon_front_8x8.png')
# Entire score and all effects are synthesized here, with a deterministic noise seed.
RATE=44100
rng=np.random.default_rng(20261126)
def tone(freq,seconds,volume=.12):
    t=np.arange(round(seconds*RATE))/RATE
    env=np.minimum(1,t/.008)*np.minimum(1,(seconds-t)/.04)
    return np.sin(2*np.pi*freq*t)*env*volume
music=np.zeros(RATE*16)
# An original syncopated eight-bar motif in D minor, composed for this game.
notes=[62,69,65,72,67,65,60,69, 62,67,70,65,74,69,67,60,
       65,72,69,62,70,67,64,69, 60,67,65,72,69,64,62,57]
for i,note in enumerate(notes):
    start=round(i*.5*RATE);seg=tone(440*2**((note-69)/12),.31,.045)
    music[start:start+len(seg)]+=seg
    bass=tone(73.416 if i<16 else 87.307,.4,.035);music[start:start+len(bass)]+=bass
    click=rng.uniform(-1,1,2205)*np.exp(-np.arange(2205)/350)*.025;music[start:start+2205]+=click
DUR={'ready':5.591,'player':.5,'enemy':.5,'enemy2':.5,'hit':.5,'playerhit':.5,'enemyhit':.5,'level':.5,'death':1,'gameover':2.624,'music':8,'bossstart':4.25,'bossfinish':4.5,'bossfail':3.25}
def effect(name):
    size=round(DUR[name]*RATE);out=np.zeros(size)
    if name=='music':return out
    if name in ['player','enemy','enemy2','hit','playerhit','enemyhit']:
        t=np.arange(size)/RATE;freq={'player':530,'enemy':170,'enemy2':230,'hit':90,'playerhit':125,'enemyhit':105}[name]
        out=(rng.uniform(-1,1,size)*.10+np.sin(2*np.pi*(freq*t-70*t*t))*.15)*np.exp(-t*22)
    else:
        melody={'ready':[62,62,65,69],'level':[74,81,86],'death':[62,57,50,38],
        'gameover':[65,62,57,50],'bossstart':[38,45,50,53,57,50],
        'bossfinish':[62,65,69,74,77,81,86],'bossfail':[50,53,49,52,45]}[name]
        step=DUR[name]/(len(melody)+1)
        for i,n in enumerate(melody):
            seg=tone(440*2**((n-69)/12),step*.7,.18);start=round(i*step*RATE)
            out[start:start+len(seg)]+=seg[:size-start]
    return out
special={'ready','gameover','bossstart','bossfinish','bossfail'}
for name in DUR:
    fx=effect(name)
    for phase in ([None] if name in special else range(64)):
        data=fx.copy()
        if phase is not None and name!='death':data+=music[(np.arange(len(data))+round(phase*.25*RATE))%len(music)]
        filename=name+('' if phase is None else '_'+str(phase))+'.snd'
        (root/'sounds'/filename).write_bytes((np.clip(data,-.9,.9)*32767).astype('<i2').tobytes())
# Review sheet is outside the packaged image directory.
review=Image.new('RGB',(600,390),'#0A142B');d=ImageDraw.Draw(review)
for row,actor in enumerate(colors):
    for col,pose in enumerate(['idle','walk1','punch','kick','down']):
        f=images[actor,pose,'r','front'];review.paste(f.resize((100,70),Image.Resampling.NEAREST),(col*110,row*78+8),f.resize((100,70),Image.Resampling.NEAREST))
        if row==0:d.text((col*110,0),pose,fill='white')
review.save(root/'original-art-preview.png')
print('Generated original sprites, background, animations and synthesized score/effects.')
