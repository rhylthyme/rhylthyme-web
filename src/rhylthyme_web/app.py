#!/usr/bin/env python3
"""
Web application for uploading and visualizing Rhylthyme programs.

Run with: python -m rhylthyme_web.app
Or after install: rhylthyme-web
"""

import os
import json
import tempfile
import urllib.request
from pathlib import Path
from flask import Flask, request, render_template_string, send_file, redirect, url_for, jsonify

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from rhylthyme_web.web.web_visualizer import generate_dag_visualization

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

MAIN_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rhylthyme Visualizer</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --brand-primary: #6B9E7D;
            --brand-primary-hover: #5a8a6b;
            --brand-primary-light: #e8f5ed;
            --brand-primary-border: #6B9E7D;
        }

        * { box-sizing: border-box; }

        .sidebar {
            transition: width 0.3s ease, transform 0.3s ease;
            width: 320px;
            min-width: 320px;
        }

        .sidebar.collapsed {
            width: 0;
            min-width: 0;
            overflow: hidden;
        }

        .sidebar-toggle {
            position: fixed;
            left: 320px;
            top: 50%;
            transform: translateY(-50%);
            width: 40px;
            height: 80px;
            background: var(--brand-primary);
            border-radius: 0 8px 8px 0;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: white;
            z-index: 100;
            transition: left 0.3s ease, background 0.2s;
        }

        .sidebar-toggle:hover {
            background: var(--brand-primary-hover);
        }

        .sidebar-toggle.collapsed {
            left: 0;
        }

        .main-content {
            transition: margin-left 0.3s ease;
        }

        .drop-zone {
            border: 2px dashed #cbd5e1;
            border-radius: 8px;
            padding: 24px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
            background: #f8fafc;
        }

        .drop-zone:hover, .drop-zone.dragover {
            border-color: var(--brand-primary);
            background: var(--brand-primary-light);
        }

        .drop-zone input[type="file"] { display: none; }

        .example-link {
            display: block;
            padding: 8px 12px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 13px;
            color: #374151;
            background: #f3f4f6;
            transition: all 0.2s;
        }

        .example-link:hover {
            background: #e5e7eb;
            color: var(--brand-primary);
        }

        .examples-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .examples-header h2 {
            margin: 0;
        }

        .examples-toggle {
            width: 28px;
            height: 28px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            background: #f9fafb;
            color: #6b7280;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .examples-toggle:hover {
            background: #f3f4f6;
            border-color: #9ca3af;
            color: var(--brand-primary);
        }

        .examples-toggle i {
            font-size: 12px;
            transition: transform 0.3s ease;
        }

        .examples-toggle.collapsed i {
            transform: rotate(180deg);
        }

        .examples-content {
            max-height: 500px;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }

        .examples-content.collapsed {
            max-height: 0;
        }

        .spinner {
            border: 3px solid #e5e7eb;
            border-top: 3px solid var(--brand-primary);
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        #visualization-frame {
            width: 100%;
            height: 100%;
            border: none;
        }

        .welcome-screen {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #6b7280;
            text-align: center;
            padding: 40px;
        }

        .welcome-screen i {
            font-size: 64px;
            margin-bottom: 24px;
            color: #d1d5db;
        }

        /* Chat Panel Styles */
        .chat-panel {
            width: 380px;
            min-width: 380px;
            transition: width 0.3s ease;
            display: flex;
            flex-direction: column;
        }

        .chat-panel.collapsed {
            width: 0;
            min-width: 0;
            overflow: hidden;
        }

        .chat-toggle {
            position: fixed;
            right: 380px;
            top: 50%;
            transform: translateY(-50%);
            width: 40px;
            height: 80px;
            background: var(--brand-primary);
            border-radius: 8px 0 0 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: white;
            z-index: 100;
            transition: right 0.3s ease, background 0.2s;
        }

        .chat-toggle:hover {
            background: var(--brand-primary-hover);
        }

        .chat-toggle.collapsed {
            right: 0;
        }

        .chat-header {
            padding: 16px;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .chat-message {
            max-width: 90%;
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.4;
        }

        .chat-message.user {
            align-self: flex-end;
            background: var(--brand-primary);
            color: white;
            border-bottom-right-radius: 4px;
        }

        .chat-message.assistant {
            align-self: flex-start;
            background: #f3f4f6;
            color: #374151;
            border-bottom-left-radius: 4px;
        }

        /* Markdown styles within chat messages */
        .chat-message.assistant p { margin: 0 0 8px 0; }
        .chat-message.assistant p:last-child { margin-bottom: 0; }
        .chat-message.assistant strong { font-weight: 600; }
        .chat-message.assistant ul, .chat-message.assistant ol {
            margin: 8px 0;
            padding-left: 20px;
        }
        .chat-message.assistant li { margin: 4px 0; }
        .chat-message.assistant code {
            background: #e5e7eb;
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 13px;
        }

        .chat-message.system {
            align-self: center;
            background: #fef3c7;
            color: #92400e;
            font-size: 12px;
            text-align: center;
        }

        .chat-input-area {
            padding: 16px;
            border-top: 1px solid #e5e7eb;
        }

        .chat-input-wrapper {
            display: flex;
            gap: 8px;
        }

        .chat-input {
            flex: 1;
            padding: 10px 14px;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }

        .chat-input:focus {
            border-color: var(--brand-primary);
        }

        .chat-send-btn {
            padding: 10px 16px;
            background: var(--brand-primary);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s;
        }

        .chat-send-btn:hover {
            background: var(--brand-primary-hover);
        }

        .chat-send-btn:disabled {
            background: #9ca3af;
            cursor: not-allowed;
        }

        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 10px 14px;
            background: #f3f4f6;
            border-radius: 12px;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
        }

        .typing-indicator span {
            width: 8px;
            height: 8px;
            background: #9ca3af;
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out;
        }

        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-4px); }
        }

        .claude-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: #6b7280;
            background: #f3f4f6;
            padding: 4px 8px;
            border-radius: 4px;
        }
    </style>
</head>
<body class="bg-gray-100 h-screen overflow-hidden">
    <div class="flex h-full">
        <!-- Collapsible Sidebar -->
        <aside id="sidebar" class="sidebar bg-white shadow-lg h-full overflow-y-auto relative flex-shrink-0">
            <div class="p-5">
                <!-- Header -->
                <div class="mb-6">
                    <div class="flex items-center justify-between">
                        <h1 class="text-xl font-bold text-gray-800 flex items-center gap-2">
                            <i class="fas fa-seedling" style="color: var(--brand-primary);"></i>
                            Rhylthyme
                        </h1>
                        <button id="sidebar-toggle-btn" class="examples-toggle" onclick="toggleSidebar()" title="Collapse sidebar">
                            <i class="fas fa-chevron-left"></i>
                        </button>
                    </div>
                    <p class="text-sm text-gray-500 mt-1">Real-time scheduling and logistics</p>
                    <a href="https://github.com/rhylthyme" target="_blank" class="inline-flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 mt-1">
                        <i class="fab fa-github"></i> GitHub
                    </a>
                </div>

                <!-- Error message -->
                <div id="error-message" class="hidden bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4 text-sm">
                </div>

                <!-- Upload Section -->
                <div class="mb-6">
                    <h2 class="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">Upload Program</h2>
                    <div class="drop-zone" id="drop-zone">
                        <i class="fas fa-cloud-upload-alt text-3xl text-gray-400 mb-2"></i>
                        <p class="text-sm font-medium text-gray-600">Drop file here</p>
                        <p class="text-xs text-gray-400 mt-1">or click to browse</p>
                        <p class="text-xs text-gray-400 mt-2">.json, .yaml, .yml</p>
                        <input type="file" id="file-input" accept=".json,.yaml,.yml">
                    </div>
                </div>

                <!-- URL Section -->
                <div class="mb-6">
                    <h2 class="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">Load from URL</h2>
                    <div class="flex gap-2">
                        <input type="text" id="url-input" placeholder="https://..."
                               class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none" style="--tw-ring-color: var(--brand-primary);">
                        <button onclick="loadFromUrl()"
                                class="px-4 py-2 text-white rounded-lg text-sm font-medium transition-colors" style="background: var(--brand-primary);" onmouseover="this.style.background='var(--brand-primary-hover)'" onmouseout="this.style.background='var(--brand-primary)'">
                            <i class="fas fa-download"></i>
                        </button>
                    </div>
                    <p class="text-xs text-gray-400 mt-2">
                        See examples at <a href="https://github.com/rhylthyme/rhylthyme-examples" target="_blank" class="hover:text-gray-600 underline">github.com/rhylthyme/rhylthyme-examples</a>
                    </p>
                </div>

                <!-- Loading indicator -->
                <div id="loading" class="hidden flex items-center justify-center gap-3 py-4 mb-4">
                    <div class="spinner"></div>
                    <span class="text-sm text-gray-600">Generating...</span>
                </div>

                <!-- Examples Section -->
                <div>
                    <div class="examples-header">
                        <h2 class="text-sm font-semibold text-gray-600 uppercase tracking-wide">Examples</h2>
                        <button id="examples-toggle" class="examples-toggle" onclick="toggleExamples()" title="Toggle examples">
                            <i class="fas fa-chevron-up"></i>
                        </button>
                    </div>
                    <div id="examples-content" class="examples-content">
                        <div class="space-y-2">
                            <a href="#" onclick="loadExample('breakfast_schedule'); return false;" class="example-link">
                                <i class="fas fa-coffee mr-2"></i>Breakfast Schedule
                            </a>
                            <a href="#" onclick="loadExample('academy_awards_ceremony'); return false;" class="example-link">
                                <i class="fas fa-award mr-2"></i>Academy Awards
                            </a>
                            <a href="#" onclick="loadExample('lab_experiment'); return false;" class="example-link">
                                <i class="fas fa-flask mr-2"></i>Lab Experiment
                            </a>
                            <a href="#" onclick="loadExample('bakery_program_example'); return false;" class="example-link">
                                <i class="fas fa-bread-slice mr-2"></i>Bakery
                            </a>
                            <a href="#" onclick="loadExample('airport_program_example'); return false;" class="example-link">
                                <i class="fas fa-plane mr-2"></i>Airport
                            </a>
                            <a href="#" onclick="loadExample('cell_culture_experiment'); return false;" class="example-link">
                                <i class="fas fa-microscope mr-2"></i>Cell Culture
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </aside>

        <!-- Sidebar Toggle Tab -->
        <div id="sidebar-toggle-tab" class="sidebar-toggle" onclick="toggleSidebar()" title="Toggle sidebar">
            <i id="toggle-icon" class="fas fa-chevron-left"></i>
        </div>

        <!-- Main Content Area -->
        <main class="main-content flex-1 h-full overflow-hidden bg-gray-50 relative">
            <div id="welcome-screen" class="welcome-screen">
                <i class="fas fa-seedling" style="color: #b8d4c2;"></i>
                <h2 class="text-2xl font-semibold text-gray-700 mb-2">Welcome to Rhylthyme Visualizer</h2>
                <p class="text-gray-500 max-w-md">
                    Upload a program file, enter a URL, or select an example from the sidebar to generate a schedule.
                </p>
            </div>
            <iframe id="visualization-frame" class="hidden"></iframe>
            <button id="download-btn" class="hidden absolute top-4 right-4 px-4 py-2 text-white rounded-lg text-sm font-medium transition-colors shadow-lg flex items-center gap-2" style="background: var(--brand-primary);" onmouseover="this.style.background='var(--brand-primary-hover)'" onmouseout="this.style.background='var(--brand-primary)'" onclick="downloadProgram()">
                <i class="fas fa-download"></i> Download Program
            </button>
        </main>

        <!-- Chat Toggle Tab -->
        <div id="chat-toggle-tab" class="chat-toggle" onclick="toggleChat()" title="Toggle AI assistant">
            <i id="chat-toggle-icon" class="fas fa-chevron-right"></i>
        </div>

        <!-- Chat Panel -->
        <aside id="chat-panel" class="chat-panel bg-white shadow-lg h-full flex-shrink-0">
            <div class="chat-header">
                <div>
                    <h2 class="text-lg font-semibold text-gray-800 flex items-center gap-2">
                        <i class="fas fa-comments" style="color: var(--brand-primary);"></i>
                        AI Assistant
                    </h2>
                    <span class="claude-badge">
                        <i class="fas fa-robot"></i> Powered by Claude
                    </span>
                </div>
                <button class="examples-toggle" onclick="toggleChat()" title="Collapse chat">
                    <i class="fas fa-chevron-right"></i>
                </button>
            </div>
            <div id="chat-messages" class="chat-messages">
                <div class="chat-message system">
                    Describe your scheduling or logistics program in plain English, and I'll help you build it.
                </div>
            </div>
            <div class="chat-input-area">
                <div class="chat-input-wrapper">
                    <input type="text" id="chat-input" class="chat-input" placeholder="Describe your program..." />
                    <button id="chat-send-btn" class="chat-send-btn" onclick="sendChatMessage()">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
            </div>
        </aside>
    </div>

    <script>
        const sidebar = document.getElementById('sidebar');
        const toggleIcon = document.getElementById('toggle-icon');
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');
        const urlInput = document.getElementById('url-input');
        const loading = document.getElementById('loading');
        const errorMessage = document.getElementById('error-message');
        const welcomeScreen = document.getElementById('welcome-screen');
        const visualizationFrame = document.getElementById('visualization-frame');

        // Conversation history for multi-turn chat
        let chatHistory = [];

        function toggleSidebar() {
            sidebar.classList.toggle('collapsed');
            const sidebarToggleTab = document.getElementById('sidebar-toggle-tab');
            const sidebarToggleBtn = document.querySelector('#sidebar-toggle-btn i');

            if (sidebar.classList.contains('collapsed')) {
                toggleIcon.classList.remove('fa-chevron-left');
                toggleIcon.classList.add('fa-chevron-right');
                sidebarToggleTab.classList.add('collapsed');
                if (sidebarToggleBtn) {
                    sidebarToggleBtn.classList.remove('fa-chevron-left');
                    sidebarToggleBtn.classList.add('fa-chevron-right');
                }
            } else {
                toggleIcon.classList.remove('fa-chevron-right');
                toggleIcon.classList.add('fa-chevron-left');
                sidebarToggleTab.classList.remove('collapsed');
                if (sidebarToggleBtn) {
                    sidebarToggleBtn.classList.remove('fa-chevron-right');
                    sidebarToggleBtn.classList.add('fa-chevron-left');
                }
            }
        }

        function toggleExamples() {
            const examplesContent = document.getElementById('examples-content');
            const examplesToggle = document.getElementById('examples-toggle');
            examplesContent.classList.toggle('collapsed');
            examplesToggle.classList.toggle('collapsed');
        }

        function showError(message) {
            errorMessage.textContent = message;
            errorMessage.classList.remove('hidden');
            setTimeout(() => errorMessage.classList.add('hidden'), 5000);
        }

        function showLoading(show) {
            if (show) {
                loading.classList.remove('hidden');
            } else {
                loading.classList.add('hidden');
            }
        }

        function showVisualization(html) {
            welcomeScreen.classList.add('hidden');
            visualizationFrame.classList.remove('hidden');
            visualizationFrame.srcdoc = html;
        }

        // File upload handling
        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                handleFileUpload(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                handleFileUpload(fileInput.files[0]);
            }
        });

        async function handleFileUpload(file) {
            const validExtensions = ['.json', '.yaml', '.yml'];
            const ext = '.' + file.name.split('.').pop().toLowerCase();

            if (!validExtensions.includes(ext)) {
                showError('Invalid file type. Use .json, .yaml, or .yml');
                return;
            }

            showLoading(true);

            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || 'Upload failed');
                }

                const html = await response.text();
                showVisualization(html);
            } catch (err) {
                showError(err.message);
            } finally {
                showLoading(false);
                fileInput.value = '';
            }
        }

        async function loadFromUrl() {
            const url = urlInput.value.trim();

            if (!url) {
                showError('Please enter a URL');
                return;
            }

            if (!url.startsWith('http://') && !url.startsWith('https://')) {
                showError('URL must start with http:// or https://');
                return;
            }

            showLoading(true);

            try {
                const response = await fetch('/api/url', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || 'Failed to load URL');
                }

                const html = await response.text();
                showVisualization(html);
            } catch (err) {
                showError(err.message);
            } finally {
                showLoading(false);
            }
        }

        async function loadExample(name) {
            showLoading(true);

            try {
                const response = await fetch('/api/example/' + name);

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || 'Failed to load example');
                }

                const html = await response.text();
                showVisualization(html);
            } catch (err) {
                showError(err.message);
            } finally {
                showLoading(false);
            }
        }

        // Handle Enter key in URL input
        urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                loadFromUrl();
            }
        });

        // Chat functionality
        const chatPanel = document.getElementById('chat-panel');
        const chatToggleTab = document.getElementById('chat-toggle-tab');
        const chatToggleIcon = document.getElementById('chat-toggle-icon');
        const chatMessages = document.getElementById('chat-messages');
        const chatInput = document.getElementById('chat-input');
        const chatSendBtn = document.getElementById('chat-send-btn');

        // Store current program for download
        let currentProgram = null;

        function stripJsonFromResponse(text) {
            // Remove JSON code blocks from the response
            return text.replace(/```json[\s\S]*?```/g, '').trim();
        }

        function downloadProgram() {
            if (!currentProgram) {
                showError('No program to download');
                return;
            }
            const blob = new Blob([JSON.stringify(currentProgram, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = (currentProgram.programId || 'program') + '.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        function toggleChat() {
            chatPanel.classList.toggle('collapsed');
            chatToggleTab.classList.toggle('collapsed');
            if (chatPanel.classList.contains('collapsed')) {
                chatToggleIcon.classList.remove('fa-chevron-right');
                chatToggleIcon.classList.add('fa-chevron-left');
            } else {
                chatToggleIcon.classList.remove('fa-chevron-left');
                chatToggleIcon.classList.add('fa-chevron-right');
            }
        }

        function addChatMessage(content, type) {
            const msgDiv = document.createElement('div');
            msgDiv.className = `chat-message ${type}`;
            // Render markdown for assistant messages, plain text for user/system
            if (type === 'assistant' && typeof marked !== 'undefined') {
                msgDiv.innerHTML = marked.parse(content);
            } else {
                msgDiv.textContent = content;
            }
            chatMessages.appendChild(msgDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function showTypingIndicator() {
            const indicator = document.createElement('div');
            indicator.className = 'typing-indicator';
            indicator.id = 'typing-indicator';
            indicator.innerHTML = '<span></span><span></span><span></span>';
            chatMessages.appendChild(indicator);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function hideTypingIndicator() {
            const indicator = document.getElementById('typing-indicator');
            if (indicator) indicator.remove();
        }

        async function sendChatMessage() {
            const message = chatInput.value.trim();
            if (!message) return;

            addChatMessage(message, 'user');
            chatInput.value = '';
            chatSendBtn.disabled = true;
            showTypingIndicator();

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: message, history: chatHistory })
                });

                hideTypingIndicator();

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || 'Chat request failed');
                }

                const data = await response.json();

                // Add to history
                chatHistory.push({ role: 'user', content: message });

                // If a program was generated, show simple message with visualize button
                if (data.program) {
                    const programName = data.program.name || 'Your program';
                    const trackCount = data.program.tracks ? data.program.tracks.length : 0;
                    const msg = `${programName} is ready! It has ${trackCount} parallel track${trackCount !== 1 ? 's' : ''} to coordinate.`;
                    addChatMessage(msg, 'assistant');
                    chatHistory.push({ role: 'assistant', content: msg });

                    const visualizeBtn = document.createElement('button');
                    visualizeBtn.className = 'mt-2 px-3 py-1 text-white text-sm rounded';
                    visualizeBtn.style.cssText = 'background: var(--brand-primary);';
                    visualizeBtn.onmouseover = () => visualizeBtn.style.background = 'var(--brand-primary-hover)';
                    visualizeBtn.onmouseout = () => visualizeBtn.style.background = 'var(--brand-primary)';
                    visualizeBtn.textContent = 'Visualize Program';
                    visualizeBtn.onclick = () => visualizeGeneratedProgram(data.program);
                    chatMessages.lastChild.appendChild(document.createElement('br'));
                    chatMessages.lastChild.appendChild(visualizeBtn);
                } else {
                    // No program generated, show the response as-is (for clarifying questions)
                    addChatMessage(data.response, 'assistant');
                    chatHistory.push({ role: 'assistant', content: data.response });

                    // If response mentions resource constraints, add a quick-confirm button
                    if (data.response && data.response.toLowerCase().includes('resource constraint')) {
                        const confirmBtn = document.createElement('button');
                        confirmBtn.className = 'mt-2 px-3 py-1 text-white text-sm rounded';
                        confirmBtn.style.cssText = 'background: var(--brand-primary);';
                        confirmBtn.onmouseover = () => confirmBtn.style.background = 'var(--brand-primary-hover)';
                        confirmBtn.onmouseout = () => confirmBtn.style.background = 'var(--brand-primary)';
                        confirmBtn.innerHTML = '<i class="fas fa-check mr-1"></i> Looks Good - Generate';
                        confirmBtn.onclick = () => {
                            chatInput.value = 'Looks good, generate the visualization';
                            sendChatMessage();
                        };
                        chatMessages.lastChild.appendChild(document.createElement('br'));
                        chatMessages.lastChild.appendChild(confirmBtn);
                    }
                }
            } catch (err) {
                hideTypingIndicator();
                addChatMessage('Error: ' + err.message, 'system');
            } finally {
                chatSendBtn.disabled = false;
            }
        }

        async function visualizeGeneratedProgram(program) {
            // Store program for download
            currentProgram = program;
            showLoading(true);
            try {
                const response = await fetch('/api/visualize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ program: program })
                });

                if (!response.ok) {
                    const data = await response.json();
                    throw new Error(data.error || 'Visualization failed');
                }

                const html = await response.text();
                showVisualization(html);
                // Show download button
                document.getElementById('download-btn').classList.remove('hidden');
            } catch (err) {
                showError(err.message);
            } finally {
                showLoading(false);
            }
        }

        // Handle Enter key in chat input
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(MAIN_PAGE)


# API endpoints for AJAX-based visualization loading

@app.route('/api/upload', methods=['POST'])
def api_upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.endswith(('.json', '.yaml', '.yml')):
        return jsonify({'error': 'Invalid file type. Use .json, .yaml, or .yml'}), 400

    try:
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='wb', suffix=Path(file.filename).suffix, delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        # Generate visualization
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as out:
            output_path = out.name

        generate_dag_visualization(tmp_path, output_path, open_browser=False)

        # Read the generated HTML
        with open(output_path, 'r') as f:
            html_content = f.read()

        # Clean up
        os.unlink(tmp_path)
        os.unlink(output_path)

        return html_content, 200, {'Content-Type': 'text/html'}

    except Exception as e:
        return jsonify({'error': f'Error generating visualization: {str(e)}'}), 500


@app.route('/api/url', methods=['POST'])
def api_load_url():
    data = request.get_json()
    url = data.get('url', '').strip() if data else ''

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    if not url.startswith(('http://', 'https://')):
        return jsonify({'error': 'URL must start with http:// or https://'}), 400

    try:
        # Determine file extension from URL
        url_path = url.split('?')[0]
        if url_path.endswith('.yaml') or url_path.endswith('.yml'):
            suffix = '.yaml'
        else:
            suffix = '.json'

        # Download file
        with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as tmp:
            req = urllib.request.Request(url, headers={'User-Agent': 'rhylthyme-web/1.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                tmp.write(response.read())
            tmp_path = tmp.name

        # Generate visualization
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as out:
            output_path = out.name

        generate_dag_visualization(tmp_path, output_path, open_browser=False)

        # Read the generated HTML
        with open(output_path, 'r') as f:
            html_content = f.read()

        # Clean up
        os.unlink(tmp_path)
        os.unlink(output_path)

        return html_content, 200, {'Content-Type': 'text/html'}

    except urllib.error.URLError as e:
        return jsonify({'error': f'Failed to fetch URL: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error generating visualization: {str(e)}'}), 500


@app.route('/api/example/<name>')
def api_load_example(name):
    # Find example file
    examples_dir = Path(__file__).parent.parent.parent.parent / 'rhylthyme-examples' / 'programs'

    for ext in ['.json', '.yaml', '.yml']:
        example_path = examples_dir / f'{name}{ext}'
        if example_path.exists():
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as out:
                    output_path = out.name

                generate_dag_visualization(str(example_path), output_path, open_browser=False)

                # Read the generated HTML
                with open(output_path, 'r') as f:
                    html_content = f.read()

                # Clean up
                os.unlink(output_path)

                return html_content, 200, {'Content-Type': 'text/html'}
            except Exception as e:
                return jsonify({'error': f'Error: {str(e)}'}), 500

    return jsonify({'error': f'Example not found: {name}'}), 404


# Chat API endpoints
SYSTEM_PROMPT = """You are a helpful assistant that helps users create Rhylthyme programs for real-time scheduling and logistics.

Rhylthyme is a JSON-based markup language for describing real-time programs that coordinate multiple parallel tracks of work with resource constraints, timing dependencies, and flexible execution patterns. It's designed for scenarios like restaurant kitchens, laboratory workflows, manufacturing processes, and any situation requiring coordinated real-time execution.

## Program Structure

A Rhylthyme program has these key components:

### Program-Level Properties (required fields marked with *)
- `programId`*: Unique identifier (e.g., "breakfast-schedule")
- `name`*: Human-readable name
- `description`: Detailed description
- `version`: Program version (e.g., "1.0.0")
- `environmentType`: Type of environment (e.g., "kitchen", "laboratory", "manufacturing")
- `actors`: Number of available workers/operators
- `tracks`*: Array of parallel execution tracks
- `resourceConstraints`*: Array of resource usage limits
- `startTrigger`: How the program begins (type: "manual", "offset", etc.)

### Track Properties
- `trackId`*: Unique identifier
- `name`*: Human-readable name
- `description`: Detailed description
- `batch_size`: Number of iterations (default: 1)
- `steps`*: Array of sequential steps

### Step Properties
- `stepId`*: Unique identifier
- `name`*: Human-readable name
- `description`: Detailed description
- `task`: Resource/tool required (must match a resourceConstraint)
- `startTrigger`*: When this step begins
- `duration`*: How long the step takes

### Start Trigger Types
1. Program Start: `{"type": "programStart"}`
2. After Another Step: `{"type": "afterStep", "stepId": "previous-step-id"}`
3. Program Start with Offset: `{"type": "programStartOffset", "offsetSeconds": 300}`

### Duration Types
1. Fixed: `{"type": "fixed", "seconds": 60}`
2. Variable (user confirms when done):
   `{"type": "variable", "minSeconds": 60, "maxSeconds": 120, "defaultSeconds": 90, "triggerName": "step-done"}`

### Resource Constraints
Each task used in steps must have a corresponding constraint:
`{"task": "stove-burner", "maxConcurrent": 2, "description": "Stove burner usage"}`

## Example: Breakfast Schedule

```json
{
  "programId": "breakfast-schedule",
  "name": "Breakfast Schedule",
  "description": "Coordinated breakfast preparation for eggs, bacon, and toast",
  "version": "1.0.0",
  "environmentType": "kitchen",
  "actors": 2,
  "startTrigger": {"type": "manual"},
  "tracks": [
    {
      "trackId": "scrambled-eggs",
      "name": "Scrambled Eggs",
      "steps": [
        {
          "stepId": "eggs-crack-whisk",
          "name": "Crack and Whisk Eggs",
          "description": "Crack eggs into bowl, whisk with salt and pepper",
          "startTrigger": {"type": "programStart"},
          "duration": {"type": "fixed", "seconds": 60},
          "task": "prep-work"
        },
        {
          "stepId": "eggs-cook",
          "name": "Cook Eggs",
          "description": "Cook eggs in pan until done",
          "startTrigger": {"type": "afterStep", "stepId": "eggs-crack-whisk"},
          "duration": {"type": "variable", "minSeconds": 120, "maxSeconds": 180, "defaultSeconds": 150, "triggerName": "eggs-done"},
          "task": "stove-burner"
        }
      ]
    },
    {
      "trackId": "bacon",
      "name": "Bacon",
      "steps": [
        {
          "stepId": "bacon-prep",
          "name": "Prepare Bacon",
          "description": "Place bacon strips in cold pan",
          "startTrigger": {"type": "programStart"},
          "duration": {"type": "fixed", "seconds": 60},
          "task": "prep-work"
        },
        {
          "stepId": "bacon-cook",
          "name": "Cook Bacon",
          "description": "Cook until crispy, flipping occasionally",
          "startTrigger": {"type": "afterStep", "stepId": "bacon-prep"},
          "duration": {"type": "variable", "minSeconds": 480, "maxSeconds": 720, "defaultSeconds": 600, "triggerName": "bacon-done"},
          "task": "stove-burner"
        }
      ]
    }
  ],
  "resourceConstraints": [
    {"task": "stove-burner", "maxConcurrent": 2, "description": "Stove burners available"},
    {"task": "prep-work", "maxConcurrent": 2, "description": "Preparation workspace"}
  ]
}
```

## Example: Laboratory Experiment

```json
{
  "programId": "lab-experiment",
  "name": "Basic Laboratory Experiment",
  "description": "Laboratory workflow for DNA analysis",
  "version": "1.0.0",
  "environmentType": "laboratory",
  "startTrigger": {"type": "manual"},
  "tracks": [
    {
      "trackId": "sample-prep",
      "name": "Sample Preparation",
      "steps": [
        {
          "stepId": "extract-dna",
          "name": "Extract DNA",
          "description": "Extract DNA from tissue samples",
          "startTrigger": {"type": "programStart"},
          "duration": {"type": "fixed", "seconds": 1800},
          "task": "bench-space"
        },
        {
          "stepId": "quantify-dna",
          "name": "Quantify DNA",
          "description": "Measure DNA concentration",
          "startTrigger": {"type": "afterStep", "stepId": "extract-dna"},
          "duration": {"type": "fixed", "seconds": 600},
          "task": "spectrophotometer"
        }
      ]
    },
    {
      "trackId": "pcr",
      "name": "PCR Amplification",
      "steps": [
        {
          "stepId": "prepare-pcr",
          "name": "Prepare PCR Mix",
          "description": "Prepare master mix",
          "startTrigger": {"type": "afterStep", "stepId": "quantify-dna"},
          "duration": {"type": "fixed", "seconds": 900},
          "task": "bench-space"
        },
        {
          "stepId": "run-pcr",
          "name": "Run PCR",
          "description": "Thermal cycling",
          "startTrigger": {"type": "afterStep", "stepId": "prepare-pcr"},
          "duration": {"type": "fixed", "seconds": 7200},
          "task": "pcr-machine"
        }
      ]
    }
  ],
  "resourceConstraints": [
    {"task": "bench-space", "maxConcurrent": 4, "description": "Bench workspace"},
    {"task": "spectrophotometer", "maxConcurrent": 1, "description": "Spectrophotometer"},
    {"task": "pcr-machine", "maxConcurrent": 2, "description": "PCR machines"}
  ]
}
```

## Guidelines

When the user describes what they want to schedule:
1. Ask clarifying questions if the workflow is unclear
2. Identify parallel tracks that can run simultaneously
3. Define proper dependencies between steps
4. Set appropriate resource constraints
5. Generate valid Rhylthyme JSON

IMPORTANT: Before calling the visualize_program tool, you MUST:
1. Briefly describe the tracks you'll create and how timing will be coordinated
2. List the **Resource Constraints** you're assuming, formatted clearly like:

   **Resource Constraints:**
   - oven: max 1 concurrent (only one oven available)
   - stovetop-burner: max 4 concurrent (4 burners on the stove)
   - prep-counter: max 2 concurrent (limited counter space)

3. Ask: "Do these resource constraints look correct? Let me know if you'd like to adjust any limits before I generate the visualization."

If the user confirms or says something like "looks good", "yes", "generate it", then call the visualize_program tool.
If the user wants changes, incorporate their feedback and show the updated constraints before generating.

IMPORTANT: Do NOT output raw JSON in your response. Use the visualize_program tool to display the program.

Keep durations realistic (in seconds). Common conversions:
- 1 minute = 60 seconds
- 5 minutes = 300 seconds
- 30 minutes = 1800 seconds
- 1 hour = 3600 seconds
- 2 hours = 7200 seconds"""


# Tool definition for visualizing programs
VISUALIZE_TOOL = {
    "name": "visualize_program",
    "description": "Creates and displays an interactive schedule visualization from a Rhylthyme program. Call this tool when you have designed a complete program and want to show it to the user.",
    "input_schema": {
        "type": "object",
        "properties": {
            "program": {
                "type": "object",
                "description": "The complete Rhylthyme program JSON object",
                "properties": {
                    "programId": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "version": {"type": "string"},
                    "environmentType": {"type": "string"},
                    "startTrigger": {"type": "object"},
                    "tracks": {"type": "array"},
                    "resourceConstraints": {"type": "array"},
                    "actors": {"type": "integer"}
                },
                "required": ["programId", "name", "tracks"]
            }
        },
        "required": ["program"]
    }
}


@app.route('/api/chat', methods=['POST'])
def api_chat():
    if not ANTHROPIC_AVAILABLE:
        return jsonify({'error': 'Anthropic SDK not installed. Run: pip install anthropic'}), 500

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return jsonify({'error': 'ANTHROPIC_API_KEY environment variable not set'}), 500

    data = request.get_json()
    message = data.get('message', '').strip() if data else ''
    history = data.get('history', []) if data else []  # Conversation history

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Build messages with history
        messages = []
        for h in history:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": message})

        # Call Claude with tool use enabled
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=[VISUALIZE_TOOL],
            messages=messages
        )

        # Process response - check for tool use
        program = None
        text_response = ""

        for block in response.content:
            if block.type == "text":
                text_response += block.text
            elif block.type == "tool_use" and block.name == "visualize_program":
                # Claude called the visualize tool - extract the program
                program = block.input.get("program")

        return jsonify({
            'response': text_response,
            'program': program
        })

    except Exception as e:
        return jsonify({'error': f'Chat error: {str(e)}'}), 500


@app.route('/api/visualize', methods=['POST'])
def api_visualize_program():
    data = request.get_json()
    program = data.get('program') if data else None

    if not program:
        return jsonify({'error': 'No program provided'}), 400

    try:
        # Save program to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            json.dump(program, tmp)
            tmp_path = tmp.name

        # Generate visualization
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as out:
            output_path = out.name

        generate_dag_visualization(tmp_path, output_path, open_browser=False)

        # Read the generated HTML
        with open(output_path, 'r') as f:
            html_content = f.read()

        # Clean up
        os.unlink(tmp_path)
        os.unlink(output_path)

        return html_content, 200, {'Content-Type': 'text/html'}

    except Exception as e:
        return jsonify({'error': f'Visualization error: {str(e)}'}), 500


# Legacy routes for backwards compatibility (direct file download)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index', error='No file uploaded'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index', error='No file selected'))

    if not file.filename.endswith(('.json', '.yaml', '.yml')):
        return redirect(url_for('index', error='Invalid file type. Use .json, .yaml, or .yml'))

    try:
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='wb', suffix=Path(file.filename).suffix, delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        # Generate visualization
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as out:
            output_path = out.name

        generate_dag_visualization(tmp_path, output_path, open_browser=False)

        # Clean up input
        os.unlink(tmp_path)

        return send_file(output_path, mimetype='text/html')

    except Exception as e:
        return redirect(url_for('index', error=f'Error generating visualization: {str(e)}'))


@app.route('/url', methods=['POST'])
def load_url():
    url = request.form.get('url', '').strip()

    if not url:
        return redirect(url_for('index', error='No URL provided'))

    if not url.startswith(('http://', 'https://')):
        return redirect(url_for('index', error='URL must start with http:// or https://'))

    try:
        # Determine file extension from URL
        url_path = url.split('?')[0]
        if url_path.endswith('.yaml') or url_path.endswith('.yml'):
            suffix = '.yaml'
        else:
            suffix = '.json'

        # Download file
        with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as tmp:
            req = urllib.request.Request(url, headers={'User-Agent': 'rhylthyme-web/1.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                tmp.write(response.read())
            tmp_path = tmp.name

        # Generate visualization
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as out:
            output_path = out.name

        generate_dag_visualization(tmp_path, output_path, open_browser=False)

        # Clean up input
        os.unlink(tmp_path)

        return send_file(output_path, mimetype='text/html')

    except urllib.error.URLError as e:
        return redirect(url_for('index', error=f'Failed to fetch URL: {str(e)}'))
    except Exception as e:
        return redirect(url_for('index', error=f'Error generating visualization: {str(e)}'))


@app.route('/example/<name>')
def load_example(name):
    # Find example file
    examples_dir = Path(__file__).parent.parent.parent.parent / 'rhylthyme-examples' / 'programs'

    for ext in ['.json', '.yaml', '.yml']:
        example_path = examples_dir / f'{name}{ext}'
        if example_path.exists():
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as out:
                    output_path = out.name

                generate_dag_visualization(str(example_path), output_path, open_browser=False)
                return send_file(output_path, mimetype='text/html')
            except Exception as e:
                return redirect(url_for('index', error=f'Error: {str(e)}'))

    return redirect(url_for('index', error=f'Example not found: {name}'))


def main():
    """Run the web application."""
    import argparse
    parser = argparse.ArgumentParser(description='Rhylthyme Web Visualizer')
    parser.add_argument('-p', '--port', type=int, default=5000, help='Port to run on (default: 5000)')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    print(f"Starting Rhylthyme Web Visualizer at http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
