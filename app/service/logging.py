import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_info(message_template: str, **kwargs):
    """
    Logs an info-level message with placeholders replaced by variables.
    Example: log_info("User {username} logged in", username="rushil")
    """
    message = message_template.format(**kwargs)
    logging.info(f"Service Log | {message}")

def log_request(message_template: str, **kwargs):
    """
    Logs an info-level message with placeholders replaced by variables.
    Example: log_info("User {username} logged in", username="rushil")
    """
    message = message_template.format(**kwargs)
    logging.info(f"Request Log | {message}")

def log_error(message_template: str, **kwargs):
    """
    Logs an error-level message with placeholders replaced by variables.
    Example: log_error("Error for user {username}: {error}", username="rushil", error="timeout")
    """
    message = message_template.format(**kwargs)
    logging.error(message)