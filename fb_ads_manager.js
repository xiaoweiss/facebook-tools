const axios = require("axios");
const { chromium } = require("playwright");

const USER_ID = "kw4udka";
const TARGET_URL =
  "https://adsmanager.facebook.com/adsmanager/manage/campaigns?act=1459530404887635&nav_entry_point=comet_bookmark&nav_source=comet";

async function checkBrowserStatus() {
  try {
    // 第一步：检测浏览器启动状态
    const statusResponse = await axios.get(
      `http://local.adspower.net:50325/api/v1/browser/active?user_id=${USER_ID}`
    );

    if (statusResponse.data.code === 0) {
      // 第二步：如果浏览器已启动，获取连接信息
      const startResponse = await axios.get(
        `http://local.adspower.net:50325/api/v1/browser/start?user_id=${USER_ID}`
      );

      if (startResponse.data.data?.ws?.puppeteer) {
        // 第三步：连接浏览器实例
        const browser = await chromium.connectOverCDP(
          startResponse.data.data.ws.puppeteer
        );
        const page = await browser.newPage();

        // 第四步：导航到目标页面
        await page.goto(TARGET_URL, { waitUntil: "networkidle" });
        console.log("成功打开广告管理页面");

        // 在此添加后续操作...
        // await browser.close(); // 操作完成后关闭
      }
    } else {
      console.log("浏览器未运行，请先启动浏览器");
    }
  } catch (error) {
    console.error("操作失败:", error.message);
  }
}

checkBrowserStatus();
