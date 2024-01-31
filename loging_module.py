import logging

logging.basicConfig(filename='logs.log',
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def log_event(event_type, event):
    if event_type == 'debug':
        logging.debug(event)
    elif event_type == 'info':
        logging.info(event)
    elif event_type == 'warning':
        logging.warning(event)
    elif event_type == 'error':
        logging.error(event)
    elif event_type == 'critical':
        logging.critical(event)
    else:
        print(f'No "{event_type}" event type. Logging it as "debug" type')
        logging.debug(event)
