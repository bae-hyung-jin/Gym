mergeInto(LibraryManager.library, {
  // WebGL 화면 바로 위에 시니어 친화적인 유튜브 인앱 팝업(iframe)을 띄운다.
  OpenYouTubeModal: function (urlPtr, titlePtr) {
    var rawUrl = UTF8ToString(urlPtr) || '';
    var title = UTF8ToString(titlePtr) || '루틴 시범 영상';

    // 유튜브 일반/짧은/쇼츠 주소를 모두 자동으로 임베드(embed) 주소로 변환
    function toEmbedUrl(u) {
      var m = u.match(/(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([A-Za-z0-9_-]{11})/);
      if (m && m[1]) {
        return 'https://www.youtube.com/embed/' + m[1] + '?autoplay=1&rel=0&modestbranding=1&playsinline=1';
      }
      return u;
    }

    var embedUrl = toEmbedUrl(rawUrl);

    // 기존 팝업이 열려 있으면 먼저 제거
    var old = document.getElementById('miribom-yt-modal');
    if (old) old.remove();

    var overlay = document.createElement('div');
    overlay.id = 'miribom-yt-modal';
    overlay.style.cssText = [
      'position:fixed', 'inset:0', 'z-index:99999',
      'background:rgba(15,23,42,0.78)',
      'display:flex', 'align-items:center', 'justify-content:center',
      'padding:20px', 'box-sizing:border-box',
      'font-family:"Noto Sans KR","Malgun Gothic",sans-serif'
    ].join(';');

    var card = document.createElement('div');
    card.style.cssText = [
      'width:100%', 'max-width:880px',
      'background:#FFFDF6', 'border-radius:24px',
      'padding:22px 24px 20px', 'box-sizing:border-box',
      'box-shadow:0 24px 60px rgba(0,0,0,0.45)',
      'display:flex', 'flex-direction:column', 'gap:14px'
    ].join(';');

    // 상단 제목 바
    var header = document.createElement('div');
    header.style.cssText = 'display:flex;align-items:center;justify-content:space-between;gap:12px;';

    var titleEl = document.createElement('div');
    titleEl.textContent = title;
    titleEl.style.cssText = 'font-size:22px;font-weight:700;color:#1E293B;';
    header.appendChild(titleEl);

    var xBtn = document.createElement('button');
    xBtn.textContent = '✕';
    xBtn.setAttribute('aria-label', '닫기');
    xBtn.style.cssText = [
      'width:42px', 'height:42px', 'border-radius:12px', 'border:none',
      'background:#EBE6D9', 'color:#1E293B', 'font-size:20px', 'font-weight:700',
      'cursor:pointer', 'flex-shrink:0'
    ].join(';');
    header.appendChild(xBtn);
    card.appendChild(header);

    // 16:9 반응형 유튜브 프레임
    var wrap = document.createElement('div');
    wrap.style.cssText = 'position:relative;width:100%;padding-top:56.25%;background:#000;border-radius:16px;overflow:hidden;';

    var iframe = document.createElement('iframe');
    iframe.src = embedUrl;
    iframe.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;border:0;';
    iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
    iframe.allowFullscreen = true;
    wrap.appendChild(iframe);
    card.appendChild(wrap);

    // 하단 큰 시니어 친화 닫기 버튼
    var closeBtn = document.createElement('button');
    closeBtn.textContent = '닫고 헬스장으로 돌아가기';
    closeBtn.style.cssText = [
      'width:100%', 'height:56px', 'border-radius:14px', 'border:none',
      'background:#FFC928', 'color:#1E293B', 'font-size:20px', 'font-weight:700',
      'cursor:pointer', 'box-shadow:0 4px 12px rgba(255,201,40,0.35)'
    ].join(';');
    card.appendChild(closeBtn);

    overlay.appendChild(card);
    document.body.appendChild(overlay);

    function closeModal() {
      var el = document.getElementById('miribom-yt-modal');
      if (el) el.remove();
      document.removeEventListener('keydown', onKey);
    }

    function onKey(e) {
      if (e.key === 'Escape') closeModal();
    }

    xBtn.onclick = closeModal;
    closeBtn.onclick = closeModal;
    overlay.onclick = function (e) {
      if (e.target === overlay) closeModal();
    };
    document.addEventListener('keydown', onKey);
  },

  CloseYouTubeModal: function () {
    var el = document.getElementById('miribom-yt-modal');
    if (el) el.remove();
  }
});
