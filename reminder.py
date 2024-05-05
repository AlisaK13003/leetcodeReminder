import requests
import webbrowser
import random
import datetime
import schedule
import time
import json
import os
import logging
import subprocess

logging.basicConfig(filename='leetcode_reminder.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Constants and Configurations
LEETCODE_URL = "https://leetcode.com"
GRAPHQL_ENDPOINT = "https://leetcode.com/graphql"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # Update this path to the actual Chrome executable
USERNAME = "koibaa"  # Hard-code your username here
PROBLEMS_FILE = r"C:\Users\akats\OneDrive\Documents\Projects\github\leetcodeReminder\leetcode_problems.json"
SCHEDULE_FILE = r"C:\Users\akats\OneDrive\Documents\Projects\github\leetcodeReminder\schedule_time.json"

def get_random_time():
    hour = random.randint(8, 20)  # 8 AM to 8 PM
    minute = random.randint(0, 59)
    return datetime.time(hour, minute)

def fetch_difficulty_stats(username):
    query = """
    {
      matchedUser(username: "%s") {
        submitStats: submitStatsGlobal {
          acSubmissionNum {
            difficulty
            count
          }
        }
      }
    }
    """ % username
    response = requests.post(GRAPHQL_ENDPOINT, json={'query': query})
    stats = response.json()['data']['matchedUser']['submitStats']['acSubmissionNum']
    least_attempted = sorted(stats, key=lambda x: x['count'])[0]['difficulty']
    return least_attempted.lower()  # 'easy', 'medium', or 'hard'

def load_problems(difficulty):
    if not os.path.exists(PROBLEMS_FILE):
        raise FileNotFoundError("The problems file does not exist. Please initialize it.")
    with open(PROBLEMS_FILE, 'r') as file:
        problems = json.load(file)
    if not problems[difficulty]:  # If the list for this difficulty is empty
        print(f"No more problems under {difficulty}. Consider resetting the file.")
        return None  # or reset automatically if desired
    return problems

def save_problems(problems):
    with open(PROBLEMS_FILE, 'w') as file:
        json.dump(problems, file)

def open_random_problem(difficulty):
    problems = load_problems(difficulty)
    if problems is None:
        return  # No problem available to open
    problem_url = problems[difficulty].pop(random.randrange(len(problems[difficulty])))  # Select and remove a random problem
    save_problems(problems)
    subprocess.Popen([CHROME_PATH, problem_url])

def daily_task():
    logging.info("Executing daily task...")
    try:
        difficulty = fetch_difficulty_stats(USERNAME)
        open_random_problem(difficulty)
        logging.info(f"Opened a problem from {difficulty} difficulty.")
    except Exception as e:
        logging.error(f"Failed to execute daily task: {e}")

def save_schedule_time(schedule_time):
    data = {"time": schedule_time.strftime("%H:%M"), "date": schedule_time.date().isoformat()}
    with open(SCHEDULE_FILE, 'w') as file:
        json.dump(data, file)

def load_schedule_time():
    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, 'r') as file:
                data = json.load(file)
                scheduled_time = datetime.datetime.strptime(data["date"] + " " + data["time"], "%Y-%m-%d %H:%M")
                return scheduled_time
        except json.JSONDecodeError:
            pass  # File is empty or data is corrupted, handle below
    return None  # Return None if file doesn't exist or is empty

def get_or_create_schedule_time():
    scheduled_time = load_schedule_time()
    if scheduled_time and scheduled_time.date() == datetime.datetime.now().date():
        return scheduled_time
    # Create a new schedule time for today
    new_time = datetime.datetime.combine(datetime.datetime.now().date(), get_random_time())
    save_schedule_time(new_time)
    return new_time

def check_and_run_missed_task():
    scheduled_time = get_or_create_schedule_time()
    current_time = datetime.datetime.now()
    if current_time >= scheduled_time:
        daily_task()  # Run immediately if the scheduled time has passed or it's time
        next_day = datetime.datetime.now() + datetime.timedelta(days=1)
        scheduled_time = datetime.datetime.combine(next_day.date(), get_random_time())
        save_schedule_time(scheduled_time)
    schedule_daily_task(scheduled_time)

def schedule_daily_task(scheduled_time):
    next_time_str = scheduled_time.strftime("%H:%M")
    print(f"Scheduled to open a problem at {next_time_str} daily.")
    schedule.clear()
    schedule.every().day.at(next_time_str).do(daily_task)

def main():
    scheduled_time = get_or_create_schedule_time()
    current_time = datetime.datetime.now()
    print(f"Task scheduled for: {scheduled_time}")
    print(f"{current_time}")
    # Additional code to schedule or run tasks

if __name__ == "__main__":
    main()

    while True:
        schedule.run_pending()
        time.sleep(60)  # sleep for 1 minute to minimize active CPU usage
