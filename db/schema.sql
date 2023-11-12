-- SQL Script to Create Database Schema for Todo App
CREATE DATABASE htmx_fastapi;

-- Create 'users' table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,      -- Unique ID for each user (auto-incremented)
    username VARCHAR(50) UNIQUE NOT NULL, -- Username, must be unique
    email VARCHAR(100) UNIQUE NOT NULL,   -- Email, must be unique
    password_hash VARCHAR(255) NOT NULL,  -- Password hash (never store plain passwords)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- User creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP  -- Last update timestamp
);

-- Create 'todos' table
CREATE TABLE todos (
    todo_id SERIAL PRIMARY KEY,       -- Unique ID for each todo item (auto-incremented)
    user_id INT NOT NULL,             -- ID of the user who owns this todo item
    content VARCHAR(255) NOT NULL,      -- Title of the todo item
    is_completed BOOLEAN DEFAULT FALSE, -- Whether the todo item is completed
    due_date TIMESTAMP WITH TIME ZONE,  -- Optional due date for the todo item
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Todo creation timestamp
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Last update timestamp
    FOREIGN KEY (user_id) REFERENCES users(user_id)  -- Foreign key to users table
);

-- Optional: Create index on the 'user_id' in 'todos' table for faster queries
CREATE INDEX idx_todos_user_id ON todos(user_id);
