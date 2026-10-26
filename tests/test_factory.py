# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 5

from tasktracker import create_app


def test_config():
    assert not create_app().testing
    assert create_app({"TESTING": True}).testing


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome to Task Tracker" in response.data


def test_about(client):
    response = client.get("/about")
    assert response.status_code == 200
    assert b"INF601" in response.data
