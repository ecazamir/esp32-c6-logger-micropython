import sys, os, machine, utime

ctime = rtc.datetime()
print(
    f"Date/time at main start: {ctime[0]:04d}-{ctime[1]:02d}-{ctime[2]:02d} {ctime[4]:02d}:{ctime[5]:02d}:{ctime[6]:02d}.{ctime[7]:06d}"
)


def get_timestamp():
    # This is used to populate log entries
    # Returns date and time as string, relative to UTC
    mdt = machine.RTC().datetime()
    timestamp_string = (
        f"{mdt[0]:04d}-{mdt[1]:02d}-{mdt[2]:02d}T{mdt[4]:02d}:{mdt[5]:02d}:{mdt[6]:02d}"
    )
    return timestamp_string


def get_log_file_name():
    mdt = machine.RTC().datetime()
    date_ymd = f"{mdt[0]:04d}-{mdt[1]:02d}-{mdt[2]:02d}"
    log_file_name = f"{config.SD_Mount_Point}/log-{date_ymd}.log"
    return log_file_name


# log_data: add a parameter timer=None to implement it as a timer callback handler.
def log_data(log_file_name="", payload="log payload not set"):
    try:
        logging_platform.set_neopixel_rgb(0, 0, 8)
        # Get the timestamp
        timestamp = get_timestamp()
        # log_file_name = get_log_file_name()
        # TODO: populate the log entry here
        # Format log entry
        log_entry = f'"{timestamp}","{payload}"'

        # Write to the file
        with open(log_file_name, "a") as log_file:
            log_file.write(log_entry + "\n")
            print(f"Logged successfully: {log_file_name}: {log_entry}")
            log_file.close()

    except Exception as e:
        print("log_data: An error occurred acquiring data or saving it to the log:", e)

    logging_platform.set_neopixel_rgb(0, 0, 0)


####
# main code
# print(f"Machine type: {MACHINE_Type}")
print("Sleeping 10s to allow program termination / update")
utime.sleep(10)
print("Entering main loop")
while True:
    #    utime.sleep(1)
    try:
        mdt = machine.RTC().datetime()
        timestamp_string = f"{mdt[0]:04d}-{mdt[1]:02d}-{mdt[2]:02d}T{mdt[4]:02d}:{mdt[5]:02d}:{mdt[6]:02d}.{mdt[7]:06d}"
        log_data(log_file_name=get_log_file_name(), payload=timestamp_string)
        # TODO: Replace sleep method from utime.sleep(1) to machine.lightsleep(time_ms)
        # machine.lightsleep(850)
        utime.sleep(1)
    except KeyboardInterrupt:
        # Clean up and stop the timer on keyboard interrupt
        # log_timer.deinit()
        print("Keyboard Interrupt, terminating program")
        sys.exit(0)
