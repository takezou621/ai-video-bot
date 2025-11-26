import { google } from "googleapis";
import "dotenv/config";
import fs from "fs";

async function main() {
  const {
    YOUTUBE_CLIENT_ID,
    YOUTUBE_CLIENT_SECRET,
    YOUTUBE_REFRESH_TOKEN,
  } = process.env;

  const oauth2Client = new google.auth.OAuth2(
    YOUTUBE_CLIENT_ID,
    YOUTUBE_CLIENT_SECRET,
    "urn:ietf:wg:oauth:2.0:oob"
  );

  oauth2Client.setCredentials({
    refresh_token: YOUTUBE_REFRESH_TOKEN,
  });

  const youtube = google.youtube({
    version: "v3",
    auth: oauth2Client,
  });

  console.log("🎬 YouTube API にアクセスできるか確認中...");

  const res = await youtube.channels.list({
    part: "snippet,contentDetails",
    mine: true,
  });

  console.log("✅ アップロード可能なアカウント情報取得成功!");
  console.log(JSON.stringify(res.data, null, 2));
}

main().catch((err) => {
  console.error("❌ エラー:", err.response?.data || err);
});

