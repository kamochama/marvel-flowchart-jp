// PUBLIC v5.12.0: optional shared watch rooms. Normal browsing stays local/offline;
// this controller connects to Cloudflare only after the user creates or joins a room.
(()=>{
  const ROOM_API='https://marvel-room-worker.kamochama.workers.dev';
  const ROOM_ID_RE=/^[A-Za-z0-9_-]{22}$/;
  const CRED_PREFIX='marvelJapanSharedRoom.v1.';
  let roomState=null, memberId='', token='', displayName='', socket=null, connecting=false;
  const pendingMessages=[];
  const listeners=new Set();

  function credKey(roomId){return CRED_PREFIX+roomId}
  function loadCred(roomId){
    try{const x=JSON.parse(localStorage.getItem(credKey(roomId))||'null');return x&&x.memberId&&x.token?x:null}catch(_){return null}
  }
  function saveCred(roomId){
    if(!roomId||!memberId||!token)return;
    try{localStorage.setItem(credKey(roomId),JSON.stringify({memberId,token,displayName}))}catch(_){}
  }
  function clearCred(roomId){try{localStorage.removeItem(credKey(roomId))}catch(_){}}
  async function readResponse(res){
    let data=null;try{data=await res.json()}catch(_){}
    if(!res.ok){const e=new Error(data?.message||`HTTP ${res.status}`);e.status=res.status;e.code=data?.error||'request_failed';throw e}
    return data||{};
  }
  function emit(kind='state'){
    const detail={kind,active:!!roomState,state:roomState,memberId,displayName};
    for(const fn of listeners){try{fn(detail)}catch(_){}}
    window.dispatchEvent(new CustomEvent('marvelroomstate',{detail}));
  }
  function setState(next,kind='state'){
    roomState=next||null;
    if(roomState?.members){
      const me=roomState.members.find(m=>m.id===memberId);
      if(me?.name) displayName=me.name;
    }
    emit(kind);
  }
  function socketUrl(roomId){
    const u=new URL(`${ROOM_API}/api/rooms/${roomId}/ws`);u.protocol='wss:';
    u.searchParams.set('memberId',memberId);u.searchParams.set('token',token);return u.toString();
  }
  function connectSocket(roomId){
    if(socket){try{socket.onclose=null;socket.close()}catch(_){}socket=null}
    const ws=new WebSocket(socketUrl(roomId));socket=ws;
    ws.onopen=()=>{while(pendingMessages.length&&ws.readyState===WebSocket.OPEN){try{ws.send(JSON.stringify(pendingMessages.shift()))}catch(_){break}}};
    ws.onmessage=e=>{
      let msg;try{msg=JSON.parse(e.data)}catch(_){return}
      if(msg?.type==='state'&&msg.state)setState(msg.state,'remote');
      else if(msg?.type==='error')window.dispatchEvent(new CustomEvent('marvelroomerror',{detail:msg}));
    };
    ws.onclose=e=>{
      if(socket!==ws)return;
      socket=null;emit('disconnected');
      if(roomState&&e?.code!==1000&&e?.code!==4000)setTimeout(()=>{if(roomState&&!socket)connectSocket(roomState.roomId)},1200);
    };
    return ws;
  }
  async function join(roomId,name,opts={}){
    if(!ROOM_ID_RE.test(roomId))throw new Error('共有ルームIDが正しくありません。');
    if(connecting)throw new Error('接続処理中です。');
    connecting=true;
    try{
      const saved=opts.credential||loadCred(roomId);
      const body={displayName:String(name||saved?.displayName||'').trim()};
      if(saved?.memberId&&saved?.token){body.memberId=saved.memberId;body.token=saved.token}
      const res=await fetch(`${ROOM_API}/api/rooms/${roomId}/join`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});
      const data=await readResponse(res);
      memberId=data.memberId;token=data.token;displayName=body.displayName;setState(data.state,opts.eventKind||'joined');saveCred(roomId);connectSocket(roomId);
      return {roomId,memberId,state:roomState,reused:!!(saved?.memberId&&saved?.token)};
    }finally{connecting=false}
  }
  async function create(name){
    const res=await fetch(`${ROOM_API}/api/rooms`,{method:'POST',headers:{'content-type':'application/json'},body:'{}'});
    const data=await readResponse(res);
    return join(data.roomId,name,{credential:null,eventKind:'created'});
  }
  async function leave(){
    const rid=roomState?.roomId;
    if(socket){try{socket.onclose=null;socket.close()}catch(_){}socket=null}
    if(rid&&memberId&&token){
      try{await fetch(`${ROOM_API}/api/rooms/${rid}/leave`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({memberId,token})})}catch(_){}
      clearCred(rid);
    }
    pendingMessages.length=0;roomState=null;memberId='';token='';displayName='';emit('left');
  }
  function send(msg){if(socket&&socket.readyState===WebSocket.OPEN){socket.send(JSON.stringify(msg));return true}if(roomState){pendingMessages.push(msg);return true}return false}
  function inviteUrl(){
    if(!roomState?.roomId)return '';
    const u=new URL(location.href);u.hash=`room=${roomState.roomId}`;return u.toString();
  }
  function roomIdFromHash(){
    const m=String(location.hash||'').match(/^#room=([A-Za-z0-9_-]{22})$/);return m?m[1]:'';
  }
  function subscribe(fn){listeners.add(fn);return()=>listeners.delete(fn)}
  window.marvelSharedRoom={
    ROOM_API,
    get active(){return !!roomState},get state(){return roomState},get memberId(){return memberId},get displayName(){return displayName},
    create,join,leave,send,inviteUrl,roomIdFromHash,loadCredential:loadCred,subscribe,
    setWatched(workId,watched){return send({type:'watched:set',workId,watched:!!watched})},
    setPlan(goalIds,tier){return send({type:'plan:set',goalIds:[...(goalIds||[])],tier})},
    ping(){return send({type:'ping'})}
  };
})();
