import asyncio
from playwright.async_api import async_playwright
import os
import shutil

async def record_walkthrough():
    print("=== Starting Playwright Recorder ===")
    
    # Ensure local video directory exists
    video_dir = os.path.abspath("./scratch/raw_videos")
    os.makedirs(video_dir, exist_ok=True)
    
    async with async_playwright() as p:
        # Launch Chromium with video recording enabled
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=video_dir,
            record_video_size={"width": 1280, "height": 800}
        )
        
        page = await context.new_page()
        
        # 1. Open the app
        print("Navigating to http://localhost:8000...")
        await page.goto("http://localhost:8000")
        await asyncio.sleep(4)  # intro pause
        
        # 2. Open GitHub Modal
        print("Opening GitHub connection modal...")
        await page.locator("#connect-gh-btn").hover()
        await asyncio.sleep(1)
        await page.locator("#connect-gh-btn").click()
        await asyncio.sleep(2)
        
        # 3. Fill in username with typing delay
        print("Typing GitHub username...")
        await page.locator("#gh-username").focus()
        await page.keyboard.type("himanshu748", delay=120) # realistic typing
        await asyncio.sleep(1.5)
        
        # 4. Click Connect
        print("Connecting GitHub...")
        await page.locator("#fetch-repos-btn").hover()
        await asyncio.sleep(0.5)
        await page.locator("#fetch-repos-btn").click()
        await asyncio.sleep(4)  # wait for sidebar to populate
        
        # 5. Click reporank in sidebar to trigger analysis
        print("Selecting reporank from sidebar...")
        # Hover and select the reporank row
        repo_item = page.locator("#sidebar-repo-list button").first # gets the first repo button
        # Wait, let's select specifically the button containing "reporank" text
        reporank_item = page.locator("#sidebar-repo-list button:has-text('reporank')").first
        await reporank_item.hover()
        await asyncio.sleep(1.5)
        await reporank_item.click()
        
        # 6. Wait for analysis steps to animate
        print("Waiting for Coral query and AI analysis...")
        await asyncio.sleep(12)  # watch the progress loading steps animate
        
        # 7. Hover on action buttons (Export, Share)
        print("Hovering on results action buttons...")
        await page.locator("#export-btn").hover()
        await asyncio.sleep(1.5)
        await page.locator("#share-btn").hover()
        await asyncio.sleep(1.5)
        
        # 8. Scroll to Radar Chart & Pitch
        print("Scrolling down to Radar Chart and Pitch...")
        # Wait, let's scroll down to the radar chart
        await page.evaluate("document.querySelector('#radar-chart').scrollIntoView({ behavior: 'smooth', block: 'center' });")
        await asyncio.sleep(2)
        await page.locator("#radar-chart").hover()
        await asyncio.sleep(4)
        
        # 9. Scroll to Coral SQL Details and expand it
        print("Expanding Coral SQL query details...")
        await page.evaluate("document.querySelector('details').scrollIntoView({ behavior: 'smooth', block: 'center' });")
        await asyncio.sleep(2)
        await page.locator("details summary").hover()
        await asyncio.sleep(1)
        await page.locator("details summary").click()
        await asyncio.sleep(6)  # inspect the SQL query
        
        # 10. Wrap up
        print("Walkthrough complete, saving video...")
        await context.close()
        await browser.close()
        
        # Get path of the recorded video
        video_files = [os.path.join(video_dir, f) for f in os.listdir(video_dir) if f.endswith(".webm")]
        if video_files:
            latest_video = max(video_files, key=os.path.getctime)
            target_path = os.path.abspath("./scratch/raw_walkthrough.webm")
            shutil.copy(latest_video, target_path)
            print(f"Saved raw video to {target_path}")
        else:
            print("Error: Video was not recorded.")

if __name__ == "__main__":
    asyncio.run(record_walkthrough())
