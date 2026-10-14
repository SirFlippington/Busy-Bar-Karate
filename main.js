/* Karate — standalone BUSY Bar / JerryScript application.
   Runtime contract: busy-app/busybar-firmware, JavaScript Applications.
   Physical controls: Start=tap punch / double-tap kick; dial press=turn; Back=exit. */
var attackSerial=0, introStarted=0, lastTap=-1, tapWindow=250, urgent=false;
var APP = 'app.kungfu.endless';
var API = 'http://127.0.0.1/api/';
var INTRO_SECONDS=5.591;
var READY_SECONDS=INTRO_SECONDS-1.0;
var DUR = {ready:INTRO_SECONDS,player:.5, enemy:.5, enemy2:.5, hit:.5, playerhit:.5, enemyhit:.5, level:.5, death:1, gameover:2.624, music:8,bossstart:4.25,bossfinish:4.5,bossfail:3.25};
var SPECIAL={ready:'sounds/ready.snd',gameover:'sounds/gameover.snd',bossstart:'sounds/bossstart.snd',bossfinish:'sounds/bossfinish.snd',bossfail:'sounds/bossfail.snd'};
var SPEED={grabber:[13,14,15,16,17,18,19],brute:[8,9,10,11,12,13,14],striker:[15,17,19,21,23,25,27]};
var STOP={grabber:5,brute:7,striker:5};
var boss=null,bossCleared=0,bossLevel=0,bossFailed=false,stageStarted=0;
var runBest=0,recordPending=false,recordAnnounced=false,recordTime=0,grabbed=false;
var game = {phase:'ready', time:0, phaseTime:0, score:0, best:0, level:1, hp:8,
    face:1, pose:'idle', attack:0, cooldown:0, invincible:0, spawn:.65,
    levelFlash:0, enemies:[], particles:0, nextId:0};
var drawPromise=null, audioPromise=null, drawn={}, frameCount=0, frameMs=0, rearAt=0, poseShown={}, attackVisible=true;
var stopped=false, drawing=false, drawFailures=0, lastTick=Date.now(), tickId;
var musicEpoch=Date.now(), soundUntil=0, musicPhase=0, soundRemaining=0, soundPriority=0, audioBusy=false, nextSound=null;
var audioStarted=false, mute=false, savedBest=0;
try { game.best = Math.max(0, parseInt(localStorage.getItem('high-score'),10)||0); } catch(e) {console.log('Score read:',String(e));}
savedBest=game.best;
function request(path, body, method) {
    return fetch(new Request(API+path, {method:method||'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)})).then(function(r){
        if (!r.ok) throw new Error(path+' HTTP '+r.status);
        return r;
    });
}
function saveBest() {
    if(game.best<=savedBest)return;
    try {localStorage.setItem('high-score',String(game.best));savedBest=game.best;}
    catch(e){console.log('Score save:',String(e));}
}
function play(name, priority) {
    if(stopped||mute)return;
    if(name==='music'&&game.phase!=='play')return;
    if(game.phase==='over'&&name!=='gameover')return;
    if(soundRemaining>0 && priority<soundPriority)return;
    if(audioBusy){if(!nextSound||priority>=nextSound.priority)nextSound={name:name,priority:priority};return;}
    var phase=Math.floor(Math.max(0,Date.now()-musicEpoch)/250)%64;
    audioBusy=true; soundPriority=priority; soundRemaining=DUR[name];
    // Each effect is premixed with the same quiet music at a nearby resume point.
    musicPhase=phase*.25;
    audioPromise=request('audio/play',{application_name:APP,path:SPECIAL[name]||'sounds/'+name+'_'+phase+'.snd'}).then(function(){
        audioBusy=false;soundUntil=Date.now()+DUR[name]*1000;
        if(stopped)return;
        if(nextSound){var pending=nextSound;nextSound=null;play(pending.name,pending.priority);}
    }).catch(function(e){audioBusy=false;nextSound=null;soundRemaining=1;soundUntil=Date.now()+1000;console.log('Audio:',String(e));});
}
function reset() {
    boss=null;bossCleared=0;bossLevel=0;bossFailed=false;grabbed=false;
    runBest=game.best;recordPending=false;recordAnnounced=false;recordTime=0;
    lastTap=-1;saveBest();introStarted=Date.now();lastTick=Date.now();game.phase='ready';game.time=0;game.phaseTime=0;game.score=0;game.level=1;
    game.hp=8;game.face=1;game.pose='idle';game.attack=0;game.cooldown=0;game.invincible=0;
    game.spawn=.65;game.levelFlash=0;game.enemies=[];game.particles=0;
    soundRemaining=0;soundUntil=0;soundPriority=0;musicPhase=0;musicEpoch=Date.now()+INTRO_SECONDS*1000;nextSound=null;play('ready',4);
}
function face(direction){if(game.phase==='dead'||game.phase==='over')return;game.face=direction<0?-1:1;urgent=true;draw();}
function addScore(points){
    game.score+=points;game.best=Math.max(game.best,game.score);
    if(!recordAnnounced&&game.score>runBest){recordPending=true;recordAnnounced=true;}
    saveBest();
}
function stage(phase,sound){
    game.phase=phase;game.phaseTime=0;stageStarted=Date.now();
    game.pose='idle';game.attack=0;game.cooldown=0;lastTap=-1;
    if(sound){soundRemaining=0;soundPriority=0;play(sound,8);}urgent=true;
}
function advanceLevel(){
    var target=1+Math.floor(game.score/100);
    while(game.level<target){
        game.level++;game.levelFlash=1.5;
        if(game.level%10===0&&bossCleared<game.level){
            bossLevel=game.level;game.enemies=[];grabbed=false;
            stage('bossintro','bossstart');return true;
        }
        game.hp=Math.min(8,game.hp+1);play('level',3);
    }
    return false;
}
function startBoss(){
    var cycle=Math.floor(bossLevel/10),hp=Math.min(28,6+cycle*2);
    boss={hp:hp,maxHp:hp,x:5,direction:1,mode:'step',serial:0,motionStart:0,hit:false,stun:0,cycle:cycle};
    game.phase='play';game.phaseTime=0;game.invincible=.5;urgent=true;
}
function defeatBoss(){
    bossCleared=bossLevel;boss=null;game.hp=8;addScore(100);advanceLevel();
    stage('bosswin','bossfinish');
    if(recordPending){recordPending=false;recordTime=4.5;}
}
function damagePlayer(amount,sound){
    if(game.invincible>0||game.phase!=='play')return;
    game.hp=Math.max(0,game.hp-amount);game.invincible=.55;play(sound||'enemyhit',2);
    if(game.hp<=0)die();
}
function updateBoss(dt){
    if(!boss||!boss.motionStart)return;
    boss.stun=Math.max(0,boss.stun-dt);
    var duration=boss.mode==='step'?1.6:1.4;
    var t=Math.min(1,Math.max(0,(Date.now()-boss.motionStart)/1000/duration));
    if(boss.mode==='step'){
        var distance=t<.5?42*t:42*(1-t);
        boss.x=boss.direction>0?5+distance:67-distance;
    }else boss.x=boss.direction>0?5+62*t:67-62*t;
    // A successful hit interrupts the attack on this pass, rewarding timing.
    if(!boss.hit&&boss.stun<=0&&Math.abs(boss.x-36)<(boss.mode==='step'?11:3)){
        boss.hit=true;damagePlayer(boss.cycle>=3?2:1,'enemy2');
    }
    if(t>=1){
        if(boss.mode==='jump'){boss.direction=-boss.direction;boss.mode='step';}
        else boss.mode='jump';
        boss.serial++;boss.motionStart=0;boss.hit=false;urgent=true;
    }
}
function attack(kind, upgrade) {
    if(game.phase==='over'){reset();return true;}
    if(game.phase!=='play'||(game.cooldown>0 && !(upgrade && game.pose==='punch')))return false;
    attackSerial++;var kick=kind==='kick';attackVisible=!!(poseShown.masterf && poseShown.masterf.indexOf(':'+kind)!==-1);game.pose=kind;game.attack=kick?.40:.30;game.cooldown=kick?.40:.30;
    var reach=kick?12:8, hits=0;
    if(boss){
        var dx=boss.x-36;
        if(boss.motionStart&&dx*game.face>=-1&&Math.abs(dx)<=reach+2){
            hits++;boss.hp-=kick?2:1;boss.hit=true;boss.stun=.3;
            if(boss.hp<=0){defeatBoss();urgent=true;draw();return true;}
        }
    }
    // Front-display coordinates are the simulation's units. Resolve nearest first.
    var candidates=game.enemies.slice().sort(function(a,b){return Math.abs(a.x-36)-Math.abs(b.x-36);});
    for(var i=0;i<candidates.length;i++){
        var e=candidates[i],dx=e.x-36;
        if(e.dead||dx*game.face<0||Math.abs(dx)>reach)continue;
        if(!kick&&hits)break;
        hits++;e.hp-=kick?2:1;e.grabbing=false;e.wind=0;e.stun=.3;e.pose='idle';
        if(e.hp<=0){e.dead=.45;e.pose='hurt';addScore(e.type==='brute'?20:e.type==='striker'?15:10);}
        game.particles=.22;
    }
    if(!advanceLevel())play(hits?'playerhit':'player',2);
    urgent=true;draw();return true;
}
function die(){
    bossFailed=!!boss;game.phase='dead';game.phaseTime=0;stageStarted=Date.now();game.pose='down';saveBest();
    recordTime=0;attackSerial++;urgent=true;
    soundRemaining=0;play(bossFailed?'bossfail':'death',9);
}
function update(dt){
    game.time+=dt;game.phaseTime+=dt;
    musicPhase=Math.max(0,(Date.now()-musicEpoch)/1000)%16;soundRemaining=Math.max(0,(soundUntil-Date.now())/1000);
    recordTime=Math.max(0,recordTime-dt);
    if(recordPending&&game.phase==='play'&&!boss&&!audioBusy&&soundPriority<5){
        recordPending=false;recordTime=4.5;play('bossfinish',7);
    }
    if(!audioBusy && soundRemaining<=0 && game.phase==='play'){soundPriority=0;play('music',0);}
    if(game.phase==='ready'||game.phase==='go'){
        var introElapsed=Math.max(0,(Date.now()-introStarted)/1000);
        if(introElapsed>=INTRO_SECONDS){game.phase='play';game.phaseTime=0;soundPriority=0;soundRemaining=0;play('music',0);}
        else game.phase=introElapsed>=READY_SECONDS?'go':'ready';
        return;
    }
    if(game.phase==='bossintro'){if((Date.now()-stageStarted)/1000>=4.25)startBoss();return;}
    if(game.phase==='bosswin'){
        if((Date.now()-stageStarted)/1000>=4.5){game.phase='play';game.phaseTime=0;game.spawn=1;game.invincible=1;}
        return;
    }
    if(game.phase==='dead'){
        if((Date.now()-stageStarted)/1000>=(bossFailed?3.25:1.05)&&!audioBusy&&soundRemaining<=0){
            game.phase='over';game.phaseTime=0;nextSound=null;
            soundRemaining=0;soundPriority=0;play('gameover',10);
        }
        return;
    }
    if(game.phase!=='play')return;
    game.cooldown=Math.max(0,game.cooldown-dt);if(attackVisible)game.attack=Math.max(0,game.attack-dt);
    game.invincible=Math.max(0,game.invincible-dt);game.levelFlash=Math.max(0,game.levelFlash-dt);
    game.particles=Math.max(0,game.particles-dt);
    if(game.attack===0)game.pose='idle';
    if(boss){updateBoss(dt);return;}
    game.spawn-=dt;
    if(game.spawn<=0 && game.enemies.length<Math.min(6,2+Math.ceil(game.level/2))){
        var side=Math.random()<.5?-1:1,slot=0,used={};
        for(var si=0;si<game.enemies.length;si++)used[game.enemies[si].slot]=true;
        while(used[slot])slot++;
        var tier=Math.min(6,Math.floor((game.level-1)/3)),roll=Math.random();
        var type=game.level>=4&&roll<.25?'striker':game.level>=2&&roll<.6?'brute':'grabber';
        var speed=SPEED[type][tier];
        game.enemies.push({id:game.nextId++,slot:slot,x:side<0?-6:78,side:side,pose:'walk',dead:0,
            speed:speed,tier:tier,approach:true,motionStart:0,wind:0,cooldown:0,type:type,
            hp:type==='brute'?2:1,stun:0,grabbing:false,grabTick:0});
        game.spawn=Math.max(.38,1.05-(game.level-1)*.035)*(.8+Math.random()*.4);
    }
    grabbed=false;
    for(var i=game.enemies.length-1;i>=0;i--){
        var e=game.enemies[i];
        if(e.dead>0){e.dead-=dt;if(e.dead<=0)game.enemies.splice(i,1);continue;}
        e.cooldown=Math.max(0,e.cooldown-dt);
        if(e.stun>0){e.stun-=dt;e.pose='idle';continue;}
        var stop=STOP[e.type];
        if(e.approach){
            if(!e.motionStart)continue;
            var travel=Math.max(0,(Date.now()-e.motionStart)/1000)*e.speed;
            var start=e.side<0?-6:78,target=36+e.side*stop;
            e.x=start-e.side*Math.min(Math.abs(target-start),travel);
            e.pose='walk';
            if(travel<Math.abs(target-start))continue;
            e.x=target;e.approach=false;e.pose='idle';
        }
        var dist=Math.abs(e.x-36);
        if(dist>stop){e.x-=e.side*e.speed*dt;if(Math.abs(e.x-36)<stop)e.x=36+e.side*stop;e.pose='walk';}
        else if(e.grabbing){
            grabbed=true;e.pose='grab';e.grabTick-=dt;
            if(e.grabTick<=0){e.grabTick=Math.max(.7,1.05-game.level*.01);damagePlayer(1);}
        }else if(e.wind>0){
            e.wind-=dt;e.pose=e.type==='grabber'?'grab':e.type==='brute'?'kick':'punch';
            if(e.wind<=0){
                if(e.type==='grabber'){e.grabbing=true;e.grabTick=.25;grabbed=true;}
                else damagePlayer(e.type==='brute'?2:1);
                if(game.phase!=='play')return;
                e.cooldown=e.type==='brute'?1.4:Math.max(.55,.85-game.level*.01);
            }
        }else if(e.cooldown<=0){e.wind=e.type==='brute'?.45:e.type==='striker'?.22:.28;e.pose='idle';play(e.type==='striker'?'enemy2':'enemy',1);}
        else e.pose='idle';
    }
}
function imageElement(id,path,x,y,display,z,opacity){return {id:id,type:'image',path:'images/'+path+'.png',x:Math.round(x),y:y,display:display,z_index:z,opacity:opacity===undefined?100:opacity};}
function textElement(id,text,x,y,display,color,font,align){return {id:id,type:'text',text:text||' ',font:font||'small',x:x,y:y,display:display,color:color||'#FFFFFFFF',align:align||'top_left',z_index:30};}
function rect(id,x,y,w,h,display,color,z){return {id:id,type:'rectangle',x:x,y:y,width:w,height:h,display:display,fill:'solid',fill_colors:[color],border_width:0,z_index:z};}
function sprite(id,who,pose,direction,x,display,visible){
    var front=display==='front',width=front?20:48;
    if(who==='master' && front)return {id:id,type:'animation',path:'animations/master_front.anim',section:pose+'_'+(direction<0?'l':'r'),loop:true,x:26,y:1,display:'front',z_index:20,opacity:100};
    return {id:id,type:'animation',path:'animations/'+who+'_'+(direction<0?'l':'r')+'_'+display+'.anim',
        section:pose,loop:pose==='walk',x:Math.round((front?x:x*148/72)-width/2),
        y:front?3:40,display:display,z_index:10,opacity:visible?100:0};
}
function elements(){
    var out=[imageElement('bgf','front',0,0,'front',0)];
    var master=sprite('masterf','master',game.pose,game.face,36,'front',true);master._generation=attackSerial;out.push(master);
    if(game.phase==='dead'||game.phase==='over'){
        master.path='animations/master_fall.anim';master.section='fall_'+(game.face<0?'l':'r');
        master.loop=false;master.y=0;
    }
    for(var i=0;i<8;i++){
        var e=null;
        for(var j=0;j<game.enemies.length;j++)if(game.enemies[j].slot===i)e=game.enemies[j];
        var front;
        if(e && !e.dead && game.phase==='play'){
            front={id:'ef'+i,type:'animation',path:'animations/approach_'+e.type+'_'+(e.side<0?'r':'l')+'_'+e.tier+'.anim',
                section:e.approach?'enter':e.pose,loop:true,x:0,y:3,display:'front',z_index:10,opacity:100};
        }else front=sprite('ef'+i,e?e.type:'grabber',e?e.pose:'idle',e?-e.side:1,e?e.x:-30,'front',!!e);
        front._generation=e?e.id:-1;out.push(front);
    }
    var bossVisible=!!boss&&game.phase==='play';
    var bossElement={id:'bossf',type:'animation',path:'animations/boss_front.anim',section:bossVisible?boss.mode+'_'+(boss.direction>0?'r':'l'):'idle_r',
        loop:true,x:0,y:0,display:'front',z_index:21,opacity:bossVisible?100:0};
    bossElement._generation=bossVisible?boss.serial:-1;out.push(bossElement);
    out.push(rect('bosshp',0,15,bossVisible?Math.max(1,Math.round(72*boss.hp/boss.maxHp)):1,1,'front',bossVisible?'#FF455FFF':'#00000000',25));
    out.push(rect('healthf',0,0,Math.max(1,game.hp*3),1,'front',game.hp?'#67FF9AFF':'#00000000',20));
    out.push(textElement('levelf','L'+game.level,70,0,'front',game.levelFlash?'#FFFF00FF':'#FFFFFFFF','tiny','top_right'));
    out.push(textElement('brand','KARATE',74,0,'back','#FFFFFFFF','normal','top_mid'));
    out.push(textElement('score','SCORE '+game.score,2,17,'back','#FFFFFFFF','small'));
    out.push(textElement('level','LV '+game.level,144,17,'back','#FFFFFFFF','small','top_right'));
    out.push(textElement('best','BEST '+game.best,2,29,'back','#BBBBBBFF','small'));
    out.push(textElement('health',bossVisible?'BOSS '+boss.hp+'/'+boss.maxHp:'HP '+game.hp+'/8',144,29,'back','#FFFFFFFF','small','top_right'));
    var title=game.phase==='ready'?'READY':game.phase==='go'?'GO!':game.phase==='over'?'GAME OVER':'';
    if(game.phase==='bossintro'){
        var stageTime=(Date.now()-stageStarted)/1000;
        title=stageTime<2?'BOSS BATTLE':stageTime<3.25?'READY':'GO!';
    }else if(game.phase==='bosswin')title='BOSS BEAT!';
    var record=recordTime>0;
    out.push(textElement('titlef',title||(recordTime>3?'NEW BEST!':''),36,4,'front','#FFFF55FF',title.length>8?'tiny':'small','top_mid'));
    out.push(textElement('titleb',record?'NEW HIGH SCORE '+game.best:title||'TAP:PUNCH  2 TAPS:KICK',74,45,'back','#FFFFFFFF','tiny','top_mid'));
    out.push(textElement('turnhelp',game.phase==='bosswin'?'HEALTH FULL!':grabbed?'GRABBED! TURN + STRIKE':'DIAL PRESS: TURN',74,56,'back','#BBBBBBFF','tiny','top_mid'));
    out.push(textElement('hint',game.phase==='over'?'START: TRY AGAIN':bossVisible?'STRIKE AS HE APPROACHES':game.levelFlash?'LEVEL UP! +1 HP':'BACK: EXIT',74,73,'back','#FFFFFFFF','tiny','top_mid'));
    return out;
}
function draw(){
    if(stopped||drawing)return;
    var all=elements(),delta=[],signatures={},posesSent={},nowDraw=Date.now(),rearDue=nowDraw>=rearAt && !urgent;
    if(rearDue)rearAt=nowDraw+500;
    for(var i=0;i<all.length;i++){
        var e=all[i];
        if(e.display==='back' && !rearDue && drawn[e.id])continue;
        var signature=JSON.stringify(e);
        if(drawn[e.id]!==signature){
            if(e.type==='animation'){
                var poseKey=e.path+':'+e.section+'#'+(e._generation===undefined?'':e._generation);posesSent[e.id]=poseKey;
                // Keep active animation sections looping: this firmware does not resume a finished timer on a section change.
                // Firmware keeps the current frame when a section name is not found.
                // Avoid reloading the same frame merely to move its widget.
                if(poseShown[e.id]===poseKey)e.section='hold_current';
            }
            delete e._generation;delta.push(e);signatures[e.id]=signature;
        }
    }
    if(!delta.length){if(game.attack>0)attackVisible=true;return;}
    drawing=true;urgent=false;var started=Date.now();
    drawPromise=request('display/draw',{application_name:APP,priority:51,elements:delta}).then(function(){
        drawing=false;drawFailures=0;
        for(var id in signatures)drawn[id]=signatures[id];
        for(var pid in posesSent)poseShown[pid]=posesSent[pid];
        for(var ei=0;ei<game.enemies.length;ei++){
            var enemy=game.enemies[ei],shown=posesSent['ef'+enemy.slot];
            if(enemy.approach && !enemy.motionStart && shown && shown.indexOf(':enter#')!==-1 && shown.slice(shown.lastIndexOf('#')+1)===String(enemy.id)){
                enemy.motionStart=Date.now();
            }
        }
        if(boss&&!boss.motionStart&&posesSent.bossf&&posesSent.bossf.indexOf(':'+boss.mode+'_')!==-1&&posesSent.bossf.slice(posesSent.bossf.lastIndexOf('#')+1)===String(boss.serial))boss.motionStart=Date.now();
        if(posesSent.masterf && posesSent.masterf.indexOf(':'+game.pose)!==-1)attackVisible=true;
        frameCount++;frameMs+=Date.now()-started;
        if(frameCount===60){console.log('Karate render ms:',Math.round(frameMs/frameCount));frameCount=0;frameMs=0;}
        if(urgent)draw();
    }).catch(function(e){
        drawing=false;drawFailures++;console.log('Display:',String(e));if(drawFailures>=5)quit();
    });
}
function quit(){
    if(stopped)return;stopped=true;saveBest();nextSound=null;
    // Drain submitted frames/audio before clearing so nothing can repaint after exit.
    Promise.all([drawPromise,audioPromise]).then(function(){
        return request('audio/play',{},'DELETE').catch(function(){});
    }).then(function(){
        return request('display/draw',{application_name:APP},'DELETE').catch(function(){});
    }).then(function(){clearInterval(tickId);unbind();});
}
function startTap(){
    var now=Date.now();
    if(game.phase==='over'){lastTap=-1;reset();urgent=true;draw();return;}
    if(game.phase!=='play')return;
    if(lastTap>=0 && now-lastTap<=tapWindow){
        lastTap=-1;attack('kick',true);
    }else{
        lastTap=attack('punch',false)?now:-1;
    }
}
var unbind=listen('input',function(event){
    if(stopped||event.action!=='press')return;
    if(event.key==='start')startTap();
    else if(event.key==='ok')face(-game.face);
    else if(event.key==='back')quit();
});
reset();draw();
tickId=setInterval(function(){
    if(stopped)return;
    var now=Date.now(),dt=Math.max(0,Math.min(1,(now-lastTick)/1000));lastTick=now;
    update(dt);draw();
},50);
