import os

colls = ["v2","v3","v4","v5"]
topics = ["1","2","3"]
procs = []
for coll in colls:
    for topic in topics:
        print("\nCalling",coll, "with topic",topic)
        os.system("start /wait cmd /c python SLAVE {} {}".format(coll,topic))
        #procs.append(subprocess.Popen(["python", "SLAVE.py",coll,topic],shell=True))
    print("\n")

#for p in procs:
#    p.wait()
#while True:
#    time.sleep(100_000)