import React, { useState, useEffect, useRef } from 'react';

function App() {
  const [events, setEvents] = useState([]);
  const [boundingBoxes, setBoundingBoxes] = useState([]);
  const videoRef = useRef(null);
  const wsRef = useRef(null);
  const eventLogRef = useRef(null);

  useEffect(() => {
    // Connect to WebSocket
    const wsUrl = window.location.protocol === 'https:'
      ? `wss://${window.location.host}/ws`
      : `ws://${window.location.host}/ws`;

    console.log(`Connecting to WebSocket at ${wsUrl}`);
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      addEvent({
        type: 'system',
        message: 'Connected to alert system',
        timestamp: new Date().toISOString()
      });
    };

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('Received event:', data);

        // Add to event log
        addEvent({
          type: data.event,
          message: `${data.event} (${data.camera_id})`,
          confidence: data.confidence,
          timestamp: data.timestamp
        });

        // Update bounding boxes
        if (data.bbox) {
          const newBox = {
            id: Date.now(),
            bbox: data.bbox,
            label: data.event,
            confidence: data.confidence
          };

          setBoundingBoxes(boxes => [...boxes, newBox]);

          // Remove box after 2 seconds
          setTimeout(() => {
            setBoundingBoxes(boxes => boxes.filter(box => box.id !== newBox.id));
          }, 2000);
        }
      } catch (err) {
        console.error('Error processing message:', err);
      }
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
      addEvent({
        type: 'system',
        message: 'Disconnected from alert system',
        timestamp: new Date().toISOString()
      });
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      addEvent({
        type: 'error',
        message: 'Connection error',
        timestamp: new Date().toISOString()
      });
    };

    // Cleanup
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Auto-scroll event log
  useEffect(() => {
    if (eventLogRef.current) {
      eventLogRef.current.scrollTop = eventLogRef.current.scrollHeight;
    }
  }, [events]);

  const addEvent = (event) => {
    setEvents(prevEvents => {
      const newEvents = [...prevEvents, event];
      // Keep only the last 100 events
      if (newEvents.length > 100) {
        return newEvents.slice(-100);
      }
      return newEvents;
    });
  };

  const getEventClass = (type) => {
    if (type.includes('gun') || type.includes('knife')) {
      return 'danger';
    }
    if (type.includes('fight') || type.includes('fall')) {
      return 'warning';
    }
    return '';
  };

  const formatTimestamp = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString();
    } catch (e) {
      return timestamp;
    }
  };

  return (
    <div className="dashboard">
      <div className="video-container">
        <video
          ref={videoRef}
          autoPlay
          muted
          loop
          playsInline
          src="/sample.mp4"
          onError={(e) => {
            console.error('Video error:', e);
            // Display a placeholder when video can't be loaded
            e.target.style.display = 'none';
            const container = e.target.parentNode;
            if (!container.querySelector('.video-placeholder')) {
              const placeholder = document.createElement('div');
              placeholder.className = 'video-placeholder';
              placeholder.innerHTML = 'No video feed available';
              placeholder.style.display = 'flex';
              placeholder.style.alignItems = 'center';
              placeholder.style.justifyContent = 'center';
              placeholder.style.height = '100%';
              placeholder.style.color = '#888';
              placeholder.style.fontSize = '1.5rem';
              container.appendChild(placeholder);
            }
          }}
        />
        {boundingBoxes.map(box => {
          const [x1, y1, x2, y2] = box.bbox;
          const videoEl = videoRef.current;

          if (!videoEl) return null;

          const videoWidth = videoEl.clientWidth;
          const videoHeight = videoEl.clientHeight;

          // Calculate position relative to video container
          const style = {
            left: `${(x1 / 640) * 100}%`,
            top: `${(y1 / 480) * 100}%`,
            width: `${((x2 - x1) / 640) * 100}%`,
            height: `${((y2 - y1) / 480) * 100}%`
          };

          return (
            <div
              key={box.id}
              className="bounding-box"
              style={style}
            >
              <div style={{
                position: 'absolute',
                top: '-20px',
                left: '0',
                background: '#4ade80',
                padding: '2px 4px',
                fontSize: '10px',
                borderRadius: '2px'
              }}>
                {box.label.replace('_detected', '')} {(box.confidence * 100).toFixed(0)}%
              </div>
            </div>
          );
        })}
      </div>

      <div className="event-log" ref={eventLogRef}>
        <h2>Event Log</h2>
        {events.length === 0 ? (
          <div className="event-item">
            <span className="event-type">System</span>
            Waiting for events...
          </div>
        ) : (
          events.map((event, index) => (
            <div key={index} className={`event-item ${getEventClass(event.type)}`}>
              <div className="event-timestamp">{formatTimestamp(event.timestamp)}</div>
              <span className="event-type">{event.type}</span>
              {event.message}
              {event.confidence && (
                <span className="confidence">{(event.confidence * 100).toFixed(0)}%</span>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default App;
