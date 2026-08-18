const express = require('express');
const http = require('http');
const socketIO = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = require('socket.io')(server, {
    cors: {
      origin: "*",
      methods: ["GET", "POST"]
    }
  });

const port = 3001;

const users = {};

io.on('connection', socket => {
    const users = {}; // Keep this here, it's needed

    socket.on('join', (username) => {
      users[socket.id] = username;
      socket.broadcast.emit('userJoined', { username: username }); // Broadcast to others
    });

    socket.on('message', (data) => {
      const senderUsername = data.sender || 'Anonymous'; // Get sender from the incoming data
      io.emit('message', { sender: senderUsername, text: data.text });
      console.log(`Received message from ${senderUsername}: ${data.text}`);
    });

    socket.on('disconnect', () => {
      const username = users[socket.id];
      if (username) {
        socket.broadcast.emit('userLeft', { username: username }); // Broadcast to others
        delete users[socket.id];
      }
    });
  });

  server.listen(port, (err) => {
    if (err) {
      console.error('Error starting server:', err);
      return;
    }
    console.log(`Chat server listening on port ${port}`);
  });