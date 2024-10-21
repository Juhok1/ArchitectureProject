import os
import multiprocessing
import sysv_ipc
import random

lock = multiprocessing.Lock()
NUM_CHILDREN = 4  # Lapsiprosessien määrä
SHM_SIZE = NUM_CHILDREN * 8  # Tarvittava tila (8 tavua per int64)

def ftok():
    numberseries = ""
    for _ in range(6):
        numbers = [0,1,2,3,4,5,6,7,8,9]
        i = random.choice(numbers)
        numberseries += str(i)
    return int(numberseries)

SHM_KEY = ftok()

def scheduler(event):
    
    shm = sysv_ipc.SharedMemory(
        SHM_KEY, sysv_ipc.IPC_CREAT | sysv_ipc.IPC_EXCL, size=1024, mode=0o666
        )

        


    # Odotetaan, että init-signaali tulee
    event.wait()

    # Luetaan muistista ja dekoodataan tiedot
    shm.attach()
    data = shm.read(SHM_SIZE).decode('utf-8').strip('\x00')  # Luetaan ja siivotaan tyhjät tavut
    numbers = list(map(int, data.split(',')))  # Muutetaan lista numeroiksi
    numbers = sorted(numbers)
    print("Scheduler received numbers:", numbers)

    # Poistetaan muistisegmentti
    shm.detach()
    shm.remove()

def child_process(pipe):
    number = int(input("Give the number between 0-19: "))
    pipe.send(number)  # Lähetetään numero parent-prosessille
    pipe.close()       # Suljetaan putki lapsiprosessissa

def init(pipes, event):
    numbers = []
    i = 0
    # Luodaan lapsiprosessit
    for i in range(NUM_CHILDREN):
        pid = os.fork()  # Käytetään fork() oikein

        if pid == 0:  # Lapsiprosessi
            child_pipe = pipes[i][1]  # Lapsi käyttää lähetysputkea
            child_process(child_pipe)
            os._exit(0)  # Lapsiprosessi päättyy

    # Vanhempi prosessi lukee lapsilta saadut numerot
    for i in range(NUM_CHILDREN):
        parent_pipe = pipes[i][0]  # Vanhempi käyttää vastaanottoputkea
        received_number = parent_pipe.recv()  # Luetaan numero lapsiprosessilta
        numbers.append(received_number)

    # Liitytään jaettuun muistiin ja tallennetaan numerot merkkijonoksi
    try:
        shm = sysv_ipc.SharedMemory(SHM_KEY)
        shm.attach()
        shm.write(','.join(map(str, numbers)).encode('utf-8'))  # Muutetaan numerot merkkijonoksi
        shm.detach()
    except Exception as e:
        print("Error writing to shared memory:", e)

    # Ilmoitetaan schedulerille, että init on valmis
    event.set()

    
if __name__ == "__main__":
    # Luodaan pipe jokaiselle lapsiprosessille
    pipes = [multiprocessing.Pipe() for _ in range(NUM_CHILDREN)]

    # Luodaan synkronointitapahtuma
    event = multiprocessing.Event()
    

    # Luodaan scheduler-prosessi
    scheduler_process = multiprocessing.Process(target=scheduler, args=(event,))
    scheduler_process.start()

    # Kutsutaan init-funktiota
    init(pipes, event)

    # Odotetaan, että scheduler on valmis
    scheduler_process.join()