chrome.tabs.onUpdated.addListener((tabId, tab) => {
  if (tab.url && tab.url.includes("youtube.com/watch")) {
    chrome.tabs.sendMessage(tabId, {
      type: "NEW",
      youtubeUrl: tab.url,
    });
  }
});
