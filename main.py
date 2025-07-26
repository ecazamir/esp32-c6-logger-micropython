import sys, os, machine, utime, time

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
        log_entry = f'"{timestamp}",{payload}'

        # Write to the file
        with open(log_file_name, "a") as log_file:
            log_file.write(log_entry + "\n")
            if (config.DEBUG_MODE):
                print(f"Logged successfully: {log_file_name}: {log_entry}")
            log_file.close()
        os.sync()

    except Exception as e:
        print("log_data: An error occurred acquiring data or saving it to the log:", e)
        sys.exit(0)

    logging_platform.set_neopixel_rgb(0, 0, 0)


####
# main code
# print(f"Machine type: {MACHINE_Type}")
print(f"Sleeping {config.START_MAIN_DELAY_SECONDS}s to allow program termination / update")
utime.sleep(config.START_MAIN_DELAY_SECONDS)
print("Entering main loop")
start_time_ms = time.ticks_ms()
cycle_duration_ms = config.LOG_INTERVAL_SECONDS * 1000
next_execution_delay_ms = 0

while True:
    try:
        current_run_time_ms = time.ticks_ms()
        logging_platform.set_neopixel_rgb(4, 4, 0)
        mdt = machine.RTC().datetime()
        log_data(log_file_name=get_log_file_name(), payload=f'"{logging_platform.lipo_battery_gauge.get_voltage():.3f}","{logging_platform.lipo_battery_gauge.get_soc():.3f}","{current_run_time_ms}", "{next_execution_delay_ms}"')
        logging_platform.set_neopixel_rgb(0, 0, 0)
        next_execution_delay_ms = cycle_duration_ms - (current_run_time_ms - start_time_ms) % cycle_duration_ms
        last_run_time_ms = current_run_time_ms
        # time.sleep_ms(next_execution_delay_ms)
        machine.lightsleep(next_execution_delay_ms)
    except KeyboardInterrupt:
        # Clean up and stop the timer on keyboard interrupt
        # log_timer.deinit()
        print("Keyboard Interrupt, terminating program")
        sys.exit(0)
