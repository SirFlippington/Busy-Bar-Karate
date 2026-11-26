"""Original 180 BPM arcade score and bitcrushed synthesized combat/vocal effects.
No recordings or external melodies. Requires NumPy. Writes 44.1 kHz mono PCM.
"""
from pathlib import Path
import numpy as np
import wave
RATE=44100
root=Path(__file__).resolve().parent
sounds=root/'sounds';sounds.mkdir(exist_ok=True)
rng=np.random.default_rng(20261127)
DUR={'ready':5.591,'player':.5,'kick':.5,'enemy':.5,'enemy2':.5,'hit':.5,'playerhit':.5,'kickhit':.5,'enemyhit':.5,'level':.5,'death':1,'gameover':2.624,'music':8,'bossstart':4.25,'bossfinish':4.5,'bossfail':3.25}
def tone(freq,seconds,volume=.12):
 t=np.arange(round(seconds*RATE))/RATE
 return np.sin(2*np.pi*freq*t)*np.minimum(1,t/.005)*np.minimum(1,(seconds-t)/.025)*volume
music=np.zeros(RATE*16)
def add(dst,seg,start):
 start=round(start*RATE);n=min(len(seg),len(dst)-start)
 if n>0:dst[start:start+n]+=seg[:n]
# Original D-minor pentatonic call-and-response, with deliberate rests.
notes=[74,77,81,84,81,77,74,None,72,74,77,None,81,77,74,72,
       69,None,72,74,77,74,72,None,69,72,74,77,74,None,72,69]
beat=1/3
for i in range(96):
 note=notes[i%32];start=i*beat/2
 if note is not None:
  freq=440*2**((note-69)/12);t=np.arange(round(.155*RATE))/RATE
  # Short pulse-wave pluck with a metallic overtone: an 8-bit string timbre.
  pulse=np.where((t*freq)%1<.25,1.,-1.)
  pluck=(pulse*.7+np.sin(2*np.pi*freq*2.01*t)*.3)*np.exp(-t*24)*np.minimum(1,t/.002)*.045
  add(music,pluck,start)
 if i%2==0:
  f=73.416 if (i//16)%3!=2 else 65.406;t=np.arange(round(.22*RATE))/RATE
  triangle=2/np.pi*np.arcsin(np.sin(2*np.pi*f*t));add(music,triangle*np.exp(-t*12)*.055,start)
 if i%8 in (0,3,4,6):
  t=np.arange(round(.16*RATE))/RATE
  drum=np.sin(2*np.pi*(55*t+5*(1-np.exp(-t*30))))*np.exp(-t*24)*.09
  add(music,drum,start)
 if i%4==2:
  t=np.arange(round(.06*RATE))/RATE
  block=(np.sin(2*np.pi*820*t)+.5*np.sin(2*np.pi*1260*t))*np.exp(-t*85)*.04;add(music,block,start)
 if i%16==0:
  t=np.arange(round(.65*RATE))/RATE
  gong=sum(np.sin(2*np.pi*180*ratio*t)*np.exp(-t*(3+j)) for j,ratio in enumerate([1,1.47,2.09,2.56]))*.018
  gong*=np.minimum(1,t/.006);add(music,gong,start)
 # Noise-channel hats leave space for the melody.
 if i%2==1:
  t=np.arange(round(.025*RATE))/RATE;add(music,rng.uniform(-1,1,len(t))*np.exp(-t*120)*.018,start)
# Quantized music retains low level beneath combat and a clean 16-second loop.
music=np.round(music*255)/255
def crush(a):
 # 11.025 kHz sample-and-hold and 7-bit amplitude, at safe original output rate.
 held=np.repeat(a[::4],4)[:len(a)]
 return np.round(np.tanh(held*1.4)*63)/63

def yell(seconds=.24,pitch=280,bright=False):
 t=np.arange(round(seconds*RATE))/RATE;u=t/seconds
 # A high, sharp /w-ah/ cry: rapid pitch rise, open vowel, falling finish.
 f0=pitch*(.65+.8*(1-np.exp(-u*15))-.55*u)+8*np.sin(2*np.pi*27*t)
 phase=2*np.pi*np.cumsum(f0)/RATE;voice=np.zeros(len(t))
 opening=1-np.exp(-u*13)
 f1=300+opening*(750 if bright else 600);f2=650+opening*850
 for k in range(1,25):
  hz=k*f0
  weight=np.exp(-((hz-f1)/230)**2)+.8*np.exp(-((hz-f2)/330)**2)+.35*np.exp(-((hz-2800)/450)**2)
  voice+=np.sin(k*phase)*weight/k**.55
 voice/=max(.001,np.max(np.abs(voice)))
 env=np.minimum(1,u/.08)*np.maximum(0,1-u)**.45
 breath=rng.uniform(-1,1,len(t))*(.12*np.exp(-u*20)+.025)
 return crush((voice*.38+breath)*env)

def combat(name):
 out=np.zeros(round(.5*RATE));kick=name in ('kick','kickhit','enemy2')
 t=np.arange(len(out))/RATE;noise=rng.uniform(-1,1,len(out))
 # Broadband cloth/air swish, then a low body thud and short high impact crack.
 swish=(noise-np.roll(noise,1))*.075*np.exp(-((t-.045)/.03)**2)
 out+=swish
 if name in ('playerhit','kickhit','enemyhit','hit'):
  u=np.maximum(0,t-.075);gate=t>=.075
  out+=gate*(np.sin(2*np.pi*((65 if kick else 105)*u+3*(1-np.exp(-u*45))))*.42*np.exp(-u*24)+noise*.20*np.exp(-u*70))
 if name!='hit':
  voice=yell(.34 if kick else .19,330 if kick else (215 if name.startswith('enemy') else 285),kick)
  add(out,voice,.04 if kick else .015)
 return crush(out)
def effect(name):
 if name in ['player','kick','playerhit','kickhit','enemy','enemy2','enemyhit','hit']:return combat(name)
 out=np.zeros(round(DUR[name]*RATE))
 if name=='music':return out
 if name=='death':add(out,yell(.65,110),0);return out
 melody={'ready':[62,62,65,69],'level':[74,81,86],'gameover':[65,62,57,50],'bossstart':[38,45,50,53,57,50],'bossfinish':[62,65,69,74,77,81,86],'bossfail':[50,53,49,52,45]}[name]
 step=DUR[name]/(len(melody)+1)
 for i,n in enumerate(melody):add(out,tone(440*2**((n-69)/12),step*.7,.18),i*step)
 return out
special={'ready','gameover','bossstart','bossfinish','bossfail'}
effects={name:effect(name) for name in DUR}
for name,fx in effects.items():
 for phase in ([None] if name in special else range(64)):
  data=fx.copy()
  if phase is not None and name!='death':data+=music[(np.arange(len(data))+round(phase*.25*RATE))%len(music)]
  assert np.max(np.abs(data))<.95
  (sounds/(name+('' if phase is None else '_'+str(phase))+'.snd')).write_bytes((data*32767).astype('<i2').tobytes())
# Listening previews are excluded from device packaging by the root folder layout.
out=root/'audio-previews';out.mkdir(exist_ok=True)
def wav(name,data):
 with wave.open(str(out/(name+'.wav')),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(RATE);w.writeframes((data*32767).astype('<i2').tobytes())
wav('Background-music-180-BPM',music)
for name in ['player','kick','playerhit','kickhit','enemy','enemy2','enemyhit','death']:wav(name,effects[name])
wav('Martial-arts-yell',yell(.34,330,True))
wav('Combat-preview',np.concatenate([np.concatenate([effects[n],np.zeros(RATE//2)]) for n in ['player','kick','playerhit','kickhit','enemy','enemy2','enemyhit','death']]))
print('Generated 180 BPM kung-fu-film-inspired chiptune music and bitcrushed combat sounds; no clipping.')
