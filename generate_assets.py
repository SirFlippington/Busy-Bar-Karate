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
def original(actor,pose,amount=1):
    # Individually designed anatomy and costume; no shared recoloured base sprite.
    w,h=(24,14) if actor=='boss' else (20,14 if actor=='master' else 12)
    im=Image.new('RGBA',(w,h));d=ImageDraw.Draw(im)
    skin='#F5BD87';shade='#B87458';white='#F1F5DF';navy='#31405F'
    walking=pose.startswith('walk');step={'walk1':-1,'walk2':0,'walk3':1}.get(pose,0)
    def line(points,c,width=1):d.line(points,fill=c,width=width)
    def hand(pt):d.point(pt,fill=skin)
    # Each rig specifies different shoulder/hip heights, stance width, arm reach,
    # head shape and clothing. Feet share the baseline even while walking.
    if actor=='master':
        hip=(9,8);shoulder=(9,4);head=(9,1);cloth=white;dark='#93B8C1'
        legs=[[(9,8),(8+step,10),(6+step,13)],[(10,8),(12-step,10),(13-step,13)]]
        arms=[[(8,4),(6,6),(8,7)],[(10,4),(12,5),(13,3)]]
    elif actor=='grabber':
        hip=(8,8);shoulder=(10,5);head=(10,3);cloth='#E969A7';dark='#8E3D7F'
        legs=[[(8,8),(5+step,9),(5+step,11)],[(9,8),(11-step,10),(12-step,11)]]
        arms=[[(9,5),(11,7),(14,7)],[(11,5),(13,4),(15,5)]]
    elif actor=='brute':
        hip=(9,7);shoulder=(9,3);head=(9,0);cloth='#E99A37';dark='#995A29'
        legs=[[(8,7),(6+step,9),(6+step,11)],[(10,7),(12-step,9),(12-step,11)]]
        arms=[[(6,3),(4,5),(6,6)],[(12,3),(14,4),(14,2)]]
    elif actor=='striker':
        hip=(9,8);shoulder=(10,4);head=(11,2);cloth='#8A92D6';dark='#424B82'
        legs=[[(9,8),(6+step,9),(4+step,11)],[(10,8),(12-step,9),(13-step,11)]]
        arms=[[(9,4),(7,5),(5,4)],[(11,4),(13,6),(14,5)]]
    else:
        hip=(11,9);shoulder=(11,4);head=(11,2);cloth='#50CB9D';dark='#23785E'
        legs=[[(10,9),(9+step,11),(8+step,13)],[(12,9),(14-step,11),(15-step,13)]]
        arms=[[(9,4),(8,7),(10,7)],[(13,4),(15,5),(16,3)]]
    if pose in ('kick','leap'):
        x,y=hip
        legs[1]=[(x+1,y),(x+3,y-2),(x+round(7*amount),y-2)]
        if pose=='leap':legs[0]=[(x,y),(x-3,y+1),(x-1,y+2)]
    if pose in ('punch','grab'):
        x,y=shoulder
        reach={'master':8,'grabber':7,'brute':7,'striker':8,'boss':9}[actor]
        arms[1]=[(x+1,y),(x+3,y+1),(min(w-1,x+round(reach*amount)),y)]
        if actor=='grabber' or pose=='grab':arms[0]=[(x-1,y),(x+2,y+3),(min(w-1,x+round(reach*amount)),y+2)]
    for n,leg in enumerate(legs):
        line(leg,dark if n==0 else cloth,2);x,y=leg[-1];line([(x-1,y),(x+1,y)],skin if actor=='master' else '#C7D3DF')
    x,y=shoulder;hx,hy=hip
    if actor=='brute':
        d.polygon([(x-3,y),(x+3,y),(hx+2,hy),(hx-2,hy)],fill=cloth)
        line([(x,y),(x,hy-1)],skin,2)
    elif actor=='boss':
        d.polygon([(x-2,y),(x+2,y),(hx+4,hy+1),(hx-3,hy+1)],fill=cloth)
        line([(x+1,y),(hx-1,hy)],'#DDF0CB');line([(hx-2,hy-1),(hx+2,hy-1)],'#F5C54C')
    else:
        d.polygon([(x-1,y),(x+1,y),(hx+2,hy),(hx-1,hy)],fill=cloth)
        if actor=='master':line([(x+1,y),(hx,hy-2)],navy);line([(hx-1,hy),(hx+2,hy)],'#EA4B42');line([(hx+1,hy),(hx+2,hy+2)],'#EA4B42')
    for n,arm in enumerate(arms):
        line(arm,skin if actor=='brute' else (dark if n==0 else cloth),2 if actor in ('brute','master') else 1);hand(arm[-1])
    x,y=head
    if actor=='master':
        d.rectangle((x-1,y,x+1,y+2),fill=skin);line([(x-1,y),(x+1,y)],'#27344E');d.point((x+2,y+1),fill=skin)
        line([(x-2,y),(x-3,y+1)],'#EA4B42');d.point((x+1,y+1),fill='#27344E')
    elif actor=='grabber':
        d.polygon([(x-1,y-1),(x+1,y-1),(x+2,y+2),(x-2,y+2)],fill='#8E3D7F');line([(x,y+1),(x+2,y+1)],skin)
    elif actor=='brute':
        d.rectangle((x-1,y,x+1,y+2),fill=skin);line([(x,y+2),(x+2,y+2)],'#633B32');d.point((x+2,y+1),fill=skin)
    elif actor=='striker':
        d.rectangle((x-1,y,x+1,y+2),fill=dark);line([(x,y+1),(x+2,y+1)],'#FFE295');line([(x-2,y+2),(x-5,y+1)],'#C785DB')
    else:
        d.rectangle((x,y,x+1,y+2),fill=skin);d.polygon([(x,y-2),(x-4,y),(x+4,y)],fill='#E8C369');line([(x-4,y),(x+4,y)],'#FFF0AD');line([(x,y+3),(x+1,y+4)],white)
    if pose in ('hurt','down'):
        im=im.rotate(-25 if pose=='hurt' else -75,resample=Image.Resampling.NEAREST)
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
            # Only the attacking limb extends; head, torso and planted foot stay fixed.
            half=original(actor,pose,.55)
            if display=='back':half=half.resize((48,32),Image.Resampling.NEAREST)
            if direction=='l':half=ImageOps.mirror(half)
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
review=Image.new('RGB',(670,470),'#0A142B');d=ImageDraw.Draw(review)
labels={'master':'PLAYER','grabber':'GRABBER','brute':'GUARD','striker':'STRIKER','boss':'BOSS'}
for row,actor in enumerate(colors):
    d.text((8,row*88+55),labels[actor],fill='white')
    for col,pose in enumerate(['idle','walk1','punch','kick','down']):
        f=images[actor,pose,'r','front'];large=f.resize((f.width*4,f.height*4),Image.Resampling.NEAREST)
        review.paste(large,(90+col*112,row*88+80-large.height),large)
        if row==0:d.text((90+col*112,4),pose,fill='white')
review.save(root/'original-art-preview.png')
print('Generated original sprites, background, animations and synthesized score/effects.')
