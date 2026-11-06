#!/bin/zsh
# 双击启动 GuessTube：本地起一个小服务器（YouTube 嵌入播放需要正常网址，file:// 会报错 153）
cd "$(dirname "$0")"
PORT=8765
if ! lsof -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; then
  nohup python3 -m http.server $PORT --bind 127.0.0.1 >/dev/null 2>&1 &
  sleep 0.6
fi
open "http://127.0.0.1:$PORT/"
osascript -e 'tell application "Terminal" to close (every window whose name contains "双击启动")' >/dev/null 2>&1 &
exit 0
