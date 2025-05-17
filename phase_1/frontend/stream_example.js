const EventSource = require('eventsource');

const source = new EventSource('http://127.0.0.1:8000/scrape-stream?industry=Plumber&location=New York');


source.onmessage = (event) => {
  console.log('Message:', event.data);
};

source.addEventListener('init', (event) => {
  console.log('Init:', event.data);
});

source.addEventListener('batch', (event) => {
  console.log('Batch:', event.data);
});

source.addEventListener('done', (event) => {
  console.log('Done:', event.data);
  source.close();
});

source.onerror = (err) => {
  console.error('Error:', err);
  source.close();
};
