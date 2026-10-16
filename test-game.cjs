const fs=require('fs'),vm=require('vm'),assert=require('assert');
const path=require('path');
const root=path.join(__dirname,'build/app.kungfu.endless/');
function setup(best=5000,saved={}){
  let now=10000,handler,requests=[],store={'high-score':String(best),...saved};
  const math=Object.create(Math);math.random=()=>.95;
  const c={console,Date:{now:()=>now},Math:math,JSON,Promise,parseInt,Error,
    localStorage:{getItem:k=>store[k],setItem:(k,v)=>store[k]=v},
    Request:class{constructor(url,opts){this.url=url;this.opts=opts;}},
    fetch:r=>{requests.push(r);return Promise.resolve({ok:true,status:200});},
    listen:(kind,fn)=>{handler=fn;return()=>handler=null;},setInterval:()=>0,clearInterval:()=>{}};
  vm.createContext(c);vm.runInContext(fs.readFileSync(path.join(__dirname,'main.js'),'utf8'),c);
  const flush=()=>new Promise(r=>setImmediate(r));
  return {c,requests,store,flush,advance:async(seconds)=>{now+=seconds*1000;c.update(seconds);c.draw();await flush();},event:(key,action='press')=>handler({key,action})};
}
function foe(type='grabber',x=41,extra={}){return{id:10,slot:0,type,x,side:x<36?-1:1,pose:'idle',dead:0,hp:type==='brute'?2:1,speed:13,tier:0,approach:false,motionStart:1,wind:0,cooldown:0,stun:0,grabbing:false,grabTick:0,...extra};}
async function running(best=5000){const t=setup(best);await t.flush();t.event('start');await t.flush();await t.advance(5.7);t.c.game.spawn=100;return t;}
(async()=>{
  let menu=setup();await menu.flush();assert.equal(menu.c.game.phase,'setup');await menu.advance(20);
  assert.equal(menu.c.game.phase,'setup');assert.equal(menu.c.game.enemies.length,0);assert.equal(menu.requests.filter(r=>r.url.endsWith('audio/play')).length,0);
  menu.event('encoder','clockwise');assert.equal(menu.c.rules().name,'HARD');assert.equal(menu.store.difficulty,'2');
  menu.event('encoder','counterclockwise');assert.equal(menu.c.rules().name,'NORMAL');assert.equal(menu.c.game.best,5000);
  menu.event('ok');assert.equal(menu.c.rules().name,'HARD');assert.equal(menu.c.game.best,0);
  menu.c.addScore(20);assert.equal(menu.store['high-score-hard'],'20');assert.equal(menu.store['high-score'],'5000');
  menu=setup(5000,{difficulty:'3','high-score-insane':'200'});await menu.flush();assert.equal(menu.c.rules().name,'INSANE');assert.equal(menu.c.game.best,200);
  menu.event('start');await menu.flush();assert.equal(menu.c.game.phase,'ready');await menu.advance(4.7);assert.equal(menu.c.game.phase,'go');await menu.advance(1);assert.equal(menu.c.game.phase,'play');
  const pressures=[];
  for(let d=0;d<4;d++){
    const q=await running();q.c.difficulty=d;q.c.game.spawn=0;await q.advance(.01);
    const enemy=q.c.game.enemies[0];assert.equal(enemy.speed,q.c.SPEED[enemy.type][enemy.tier]);
    q.c.bossLevel=10;q.c.startBoss();pressures.push({spawn:q.c.game.spawn,hp:q.c.boss.hp,tier:enemy.tier});
  }
  for(let d=1;d<4;d++){assert(pressures[d].spawn<pressures[d-1].spawn);assert(pressures[d].hp>pressures[d-1].hp);assert(pressures[d].tier>=pressures[d-1].tier);}
  menu.c.game.phase='over';menu.event('ok');assert.equal(menu.c.game.phase,'setup');
  let t=await running(),c=t.c;
  t.event('encoder','counterclockwise');assert.equal(c.game.face,-1);
  t.event('encoder','clockwise');assert.equal(c.game.face,1);
  t.event('encoder','clockwise');assert.equal(c.game.face,1,'Repeated clockwise ticks keep facing right');
  t.event('ok');assert.equal(c.game.face,-1,'Dial press still reverses');t.event('ok');
  c.game.phase='dead';t.event('encoder','counterclockwise');assert.equal(c.game.face,1,'Death animation direction remains fixed');c.game.phase='play';
  assert.equal(c.game.phase,'play');c.game.enemies=[foe()];
  await t.advance(.01);assert(c.game.enemies[0].wind>0);await t.advance(.3);
  assert(c.game.enemies[0].grabbing,'Pink enemy attaches');let hp=c.game.hp;await t.advance(.3);
  assert.equal(c.game.hp,hp-1,'Grab drains health');t.event('start');assert(c.game.enemies[0].dead>0,'Punch breaks grab');
  await t.advance(.5);c.game.enemies=[foe('brute',43)];c.game.face=1;c.game.cooldown=0;c.game.attack=0;c.game.pose='idle';
  const score=c.game.score;t.event('start');assert.equal(c.game.enemies[0].hp,1);assert.equal(c.game.score,score,'Guard survives first punch');
  await t.advance(.1);t.event('start');assert.equal(c.game.pose,'kick');assert(c.game.enemies[0].dead>0);assert.equal(c.game.score,score+20);
  t.event('ok');assert.equal(c.game.face,-1);t.event('start','release');assert.equal(c.game.pose,'kick');
  await t.advance(.5);c.game.enemies=[foe('striker',31)];c.game.cooldown=0;c.attack('punch');assert(c.game.enemies[0].dead>0);
  for(const type of ['grabber','brute','striker'])for(const side of [-1,1])for(let tier=0;tier<7;tier++){
    c.game.enemies=[foe(type,side<0?-6:78,{side,tier,approach:true})];
    if(fs.existsSync(root))for(const e of c.elements())if(e.path)assert(fs.existsSync(root+e.path),e.path);
  }
  assert(c.SPEED.brute.every((n,i)=>n<c.SPEED.grabber[i]&&n<c.SPEED.striker[i]));
  t=await running();c=t.c;c.game.score=890;c.game.level=9;c.game.enemies=[foe()];c.attack('punch');
  assert.equal(c.game.phase,'bossintro');assert.equal(c.game.level,10);assert.equal(c.game.enemies.length,0);
  const title=()=>c.elements().find(e=>e.id==='titlef').text;
  assert.equal(title(),'BOSS BATTLE');await t.advance(2.1);assert.equal(title(),'READY');await t.advance(1.2);assert.equal(title(),'GO!');await t.advance(1);
  assert(c.boss&&c.boss.hp===8);assert.equal(c.game.phase,'play');assert(c.boss.motionStart>0,'Boss clocks start after the animation is submitted');
  await t.advance(.8);assert(Math.abs(c.boss.x-26)<1,'Boss steps towards the player');c.game.face=1;c.game.cooldown=0;
  const bossHp=c.boss.hp;c.attack('kick');assert.equal(c.boss.hp,bossHp,'Attacks facing away miss');c.game.face=-1;c.game.cooldown=0;c.attack('kick');assert.equal(c.boss.hp,bossHp-2);
  await t.advance(.81);assert.equal(c.boss.mode,'jump');await t.advance(.7);assert(Math.abs(c.boss.x-36)<1,'Jump crosses over player');
  await t.advance(.71);assert.equal(c.boss.direction,-1);assert.equal(c.boss.mode,'step');await t.advance(.8);assert(Math.abs(c.boss.x-46)<1,'Boss approaches from the opposite side');
  c.game.face=1;c.game.hp=1;c.game.cooldown=0;c.boss.hp=1;c.attack('kick');assert.equal(c.game.phase,'bosswin');assert.equal(c.game.hp,8);assert.equal(c.bossCleared,10);assert.equal(c.game.level,11);
  await t.advance(4.6);assert.equal(c.game.phase,'play');assert.equal(c.boss,null);assert.equal(c.game.hp,8);
  c.game.score=1890;c.game.level=19;c.game.cooldown=0;c.game.enemies=[foe()];c.attack('punch');assert.equal(c.game.phase,'bossintro');assert.equal(c.bossLevel,20);
  await t.advance(4.3);assert.equal(c.boss.maxHp,10,'Later boss has more health');
  c.game.hp=1;c.game.invincible=0;c.damagePlayer(1);await t.flush();assert(c.bossFailed);assert.equal(c.game.phase,'dead');
  assert(t.requests.some(r=>r.opts.body.includes('bossfail.snd')));await t.advance(3.3);assert.equal(c.game.phase,'over');
  assert.equal(t.requests.filter(r=>r.opts.body.includes('sounds/gameover.snd')).length,1,'Boss defeat also plays game-over cue');
  let sounds=t.requests.filter(r=>r.url.endsWith('audio/play')).length;
  await t.advance(20);assert.equal(t.requests.filter(r=>r.url.endsWith('audio/play')).length,sounds,'Stay silent after boss game over');
  t.event('start');assert.equal(c.game.phase,'ready');assert.equal(c.boss,null);assert.equal(c.bossCleared,0);
  t=await running(10);c=t.c;c.game.score=10;c.game.enemies=[foe()];c.attack('punch');await t.flush();await t.advance(.1);await t.flush();
  assert(c.recordAnnounced);assert(c.recordTime>0);assert.equal(t.store['high-score'],'20');assert(t.requests.some(r=>r.opts.body.includes('bossfinish.snd')),'New record uses celebration');
  c.game.phase='play';c.game.enemies=[];c.game.spawn=100;c.recordPending=false;
  for(let i=0;i<6;i++){await t.advance(8.4);assert(t.requests.filter(r=>r.url.endsWith('audio/play')).at(-1).opts.body.includes('music_'),'Music keeps looping');}
  c.game.phase='play';
  for(const pose of ['idle','punch','kick'])for(const face of [-1,1]){c.game.pose=pose;c.game.face=face;assert(c.elements().find(e=>e.id==='masterf').loop,'Player timer stays running');}
  c.boss=null;c.game.face=-1;c.die();await t.flush();
  let falling=c.elements().find(e=>e.id==='masterf');assert.equal(falling.path,'animations/master_fall.anim');assert.equal(falling.section,'fall_l');assert.equal(falling.loop,false);
  assert.equal(c.elements().find(e=>e.id==='titlef').text,' ','Death text must not cover the fall');
  c.face(1);assert.equal(c.game.face,-1,'Turning must not restart death animation');
  await t.advance(1.1);assert.equal(c.game.phase,'over');assert.equal(c.elements().find(e=>e.id==='masterf').path,falling.path,'Keep transparent last frame at game over');
  assert.equal(t.requests.filter(r=>r.opts.body.includes('sounds/gameover.snd')).length,1,'Ordinary defeat plays one game-over cue');
  sounds=t.requests.filter(r=>r.url.endsWith('audio/play')).length;
  c.play('music',0);c.play('bossfinish',8);
  for(let i=0;i<6;i++)await t.advance(8.4);
  assert.equal(t.requests.filter(r=>r.url.endsWith('audio/play')).length,sounds,'No background music, celebration or repeated cue after game over');
  c.reset();assert.equal(c.elements().find(e=>e.id==='masterf').path,'animations/master_front.anim','Restart restores live player');
  await t.flush();await t.advance(5.7);assert(t.requests.filter(r=>r.url.endsWith('audio/play')).at(-1).opts.body.includes('music_'),'Music restarts for a new game');
  c.quit();await t.flush();await t.flush();
  console.log('PASS: grab/escape, two-hit guards, quick strikers, controls, assets, boss warning/ready/go, footwork/jumps, facing, hits, refill, recurring bosses, boss loss, records, music loop and animation timers.');
})().catch(e=>{console.error(e);process.exitCode=1});
