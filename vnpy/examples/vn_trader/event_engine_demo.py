from time import sleep
from vnpy.event import EventEngine, Event

def handle(event: Event):
    print("recei:" + event.type)

def main():
    event_engine = EventEngine()
    event_engine.register("test", handle)
    event_engine.start()
    evt = Event("test")
    evt.data = "df"
    print("recei22:" + evt.__str__())
    event_engine.put(evt)
    sleep(1)
    event_engine.stop()

main()
