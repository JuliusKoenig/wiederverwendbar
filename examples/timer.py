from wiederverwendbar.timer import timer_loop

if __name__ == '__main__':
    try:
        while True:
            print("loop")
            timer_loop("test-loop", 1)
    except KeyboardInterrupt:
        ...

    print("end")
