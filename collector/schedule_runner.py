import time
from collector import GrokTrendsCollector

print("🔄 Starting Grok Trends scheduled collector...")
print("Running every 15 minutes. Press Ctrl+C to stop.\n")

while True:
    try:
        c = GrokTrendsCollector()
        c.run(block_on_rate_limit=True)  # Will auto-wait if rate limited
        c.close()
    except KeyboardInterrupt:
        print("\n👋 Stopping collector...")
        break
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n⏰ Sleeping for 15 minutes...")
    time.sleep(15 * 60)