"""tracker.py: the data layer of my job application tracker.

It reads two files in the data folder and builds two dictionaries that share
the same keys (one key per application, like "BrightPath - Project Coordinator"):

    applications = {key: [ {"date": ..., "status": ...}, ... ]}   oldest step first
    details      = {key: {"location": ..., "skills": [...]}}

The newest step is the last item in the list, so the current status of an
application is applications[key][-1]["status"].
"""

import csv
import os
from datetime import date

# BASE is the folder this file lives in, so the paths work from any folder.
BASE = os.path.dirname(os.path.abspath(__file__))
STEPS_FILE = os.path.join(BASE, "data", "steps.csv")
DETAILS_FILE = os.path.join(BASE, "data", "details.csv")

STATUSES = ["Applied", "Followed up", "Interview", "Offer", "Rejected", "Withdrawn"]
FINISHED = ["Offer", "Rejected", "Withdrawn"]   # nothing left to chase


# ---------- reading the files ----------

def read_rows(path):
    """Read a csv file and return a list of rows. Each row is a dict by column name."""
    with open(path, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def build_applications(path=STEPS_FILE):
    """Group the steps by application. The file must list each application's steps oldest first."""
    applications = {}
    for row in read_rows(path):
        key = row["application"]
        if key not in applications:
            applications[key] = []
        steps = applications[key]
        if len(steps) > 0 and row["date"] < steps[-1]["date"]:
            raise ValueError(key + ": step dated " + row["date"] + " comes after a newer step")
        steps.append({"date": row["date"], "status": row["status"]})
    return applications


def build_details(path=DETAILS_FILE):
    """One entry per application: its location and its list of skills."""
    details = {}
    for row in read_rows(path):
        skills = []
        for skill in row["skills"].split(";"):
            skills.append(skill.strip())
        details[row["application"]] = {"location": row["location"], "skills": skills}
    return details


# ---------- answering questions ----------

def current_status(applications, key):
    """The newest step is the last one, so its status is where the application stands."""
    return applications[key][-1]["status"]


def current_statuses(applications):
    """Where every application stands right now: {key: status}."""
    standing = {}
    for key in applications:
        standing[key] = current_status(applications, key)
    return standing


def count_by_status(applications):
    """How many applications sit at each status right now."""
    counts = {}
    for status in current_statuses(applications).values():
        if status not in counts:
            counts[status] = 0
        counts[status] = counts[status] + 1
    return counts


def days_between(start_text, end_text):
    """Whole days from one date like "2026-10-05" to another."""
    return (date.fromisoformat(end_text) - date.fromisoformat(start_text)).days


def follow_up_order(applications, today):
    """Applications still open, as (days quiet, key) pairs. The quietest one comes first."""
    waiting = []
    for key in applications:
        if current_status(applications, key) not in FINISHED:
            days = days_between(applications[key][-1]["date"], today)
            waiting.append((days, key))
    waiting.sort(reverse=True)
    return waiting


def skill_counts(details):
    """How many applications ask for each skill: {skill: count}."""
    counts = {}
    for key in details:
        for skill in details[key]["skills"]:
            if skill not in counts:
                counts[skill] = 0
            counts[skill] = counts[skill] + 1
    return counts


def top_skills(details, how_many=3):
    """The skills asked for most, as (skill, count) pairs. Ties land in reverse alphabetical order."""
    counts = skill_counts(details)
    ranked = []
    for skill in counts:
        ranked.append((counts[skill], skill))
    ranked.sort(reverse=True)
    top = []
    for count, skill in ranked[:how_many]:
        top.append((skill, count))
    return top


# ---------- changing the data ----------

def add_step(applications, key, date_text, status):
    """Add a new newest step. append() puts it on the end and leaves the older steps alone."""
    if key not in applications:
        raise ValueError("No application named " + key)
    if status not in STATUSES:
        raise ValueError(status + " is not one of " + ", ".join(STATUSES))
    date.fromisoformat(date_text)   # stops here with an error if the date is not like 2026-11-14
    if date_text < applications[key][-1]["date"]:
        raise ValueError("A new step cannot be older than the last one")
    applications[key].append({"date": date_text, "status": status})


def add_application(applications, details, key, location, skills, date_text):
    """Start a new application with its first step, "Applied"."""
    if key in applications:
        raise ValueError(key + " is already in the tracker")
    date.fromisoformat(date_text)
    applications[key] = [{"date": date_text, "status": "Applied"}]
    details[key] = {"location": location, "skills": skills}


# ---------- saving ----------

def save_steps(applications, path=STEPS_FILE):
    """Write every step of every application back to a file, oldest first."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["application", "date", "status"])
        for key in applications:
            for step in applications[key]:
                writer.writerow([key, step["date"], step["status"]])


def save_details(details, path=DETAILS_FILE):
    """Write the location and skills of every application back to a file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["application", "location", "skills"])
        for key in details:
            writer.writerow([key, details[key]["location"], ";".join(details[key]["skills"])])
