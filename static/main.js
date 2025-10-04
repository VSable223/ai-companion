(function(){
  const socket = io('/signal');
  const chat = document.getElementById('chatWindow');
  const input = document.getElementById('input');
  const sendBtn = document.getElementById('sendBtn');

  function appendBubble(text, who='ai'){
    const div = document.createElement('div');
    div.className = 'bubble ' + (who==='user' ? 'user' : 'ai');
    div.innerText = text;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
  }

  sendBtn.addEventListener('click', ()=>{
    const val = input.value.trim();
    if(!val) return;
    appendBubble(val, 'user');
    socket.emit('user_message', { text: val });
    input.value = '';
  });

  input.addEventListener('keydown', (e)=>{
    if(e.key === 'Enter') sendBtn.click();
  });

  socket.on('connect', ()=>{
    console.log('connected to server');
  });

  socket.on('ai_reply', (data)=>{
    const txt = data.text || data;
    appendBubble(txt, 'ai');
    try{
      if('speechSynthesis' in window){
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(txt);
        u.lang = 'en-US';
        u.rate = 1.0;
        u.pitch = 1.0;
        window.speechSynthesis.speak(u);
      }
    }catch(e){ console.warn('TTS failed', e); }
  });

  socket.on('disconnect', ()=>{ console.log('disconnected'); });
})();
