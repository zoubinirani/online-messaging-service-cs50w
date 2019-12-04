document.addEventListener('DOMContentLoaded', () => {

    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
   
    socket.on('message', data => {
        const li = document.createElement('li');
        li.innerHTML = `${data.username}${data.msg}${data.timenow}`;
        document.querySelector('#chat').append(li);
    });

    document.querySelector('#messages').onsubmit = () => {
        var message = document.querySelector('#message').value;
        message = ': ' + message;
        socket.emit('message_recieve', {"message": message});
        return false;
    };

});