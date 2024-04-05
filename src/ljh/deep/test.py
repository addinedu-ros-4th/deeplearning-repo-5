import pyttsx3
import time
engine = pyttsx3.init()



start = time.time()
engine.setProperty('rate', 200)

engine.say('무궁화 꽃이 피었습니다')
end = time.time()

print(end - start)

# engine.runAndWait()
while 1:
    pass