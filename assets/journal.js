(() => {
  const feed = document.querySelector('[data-social-feed]');
  if (!feed) return;
  const buttons = [...feed.querySelectorAll('[data-channel]')];
  const posts = [...feed.querySelectorAll('[data-post-channel]')];
  const fallbacks = [...feed.querySelectorAll('[data-fallback-channel]')];
  const count = feed.querySelector('[data-feed-count]');
  feed.querySelector('[data-feed-filters]').hidden = false;
  buttons.forEach(button => button.addEventListener('click', () => {
    const channel = button.dataset.channel;
    let visible = 0;
    buttons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    posts.forEach(post => {
      post.hidden = channel !== 'all' && post.dataset.postChannel !== channel;
      if (!post.hidden) visible += 1;
    });
    fallbacks.forEach(item => {
      item.hidden = visible !== 0 || item.dataset.fallbackChannel !== channel;
    });
    count.textContent = `${visible} selected ${visible === 1 ? 'post' : 'posts'}`;
  }));
})();
