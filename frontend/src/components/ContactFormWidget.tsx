import React, { useState, useEffect } from 'react';

interface ContactFormWidgetProps {
  formTitle?: string;
  submitButtonText?: string;
  // apiEndpoint?: string; // To be added later
}

const getGAClientId = (): string => {
  // In a real scenario, you might try to get this from cookies or a GA API
  // For example, by looking for a cookie like _ga or _ga_YOUR_MEASUREMENT_ID
  // Or if using analytics.js (Universal Analytics):
  // if (typeof ga === 'function' && ga.getAll && ga.getAll()[0]) {
  //   return ga.getAll()[0].get('clientId');
  // }
  // For gtag.js (GA4), it's more complex and often involves parsing cookies like _ga_MEASUREMENTID
  // or custom event tracking.
  return "CLIENT_ID_PLACEHOLDER";
};

const getGASessionId = (): string => {
  // Similar to client ID, session ID retrieval is complex.
  // For gtag.js (GA4), you might use:
  // gtag('get', 'YOUR_MEASUREMENT_ID', 'session_id', (sessionId) => { /* use sessionId */ });
  // Or parse it from cookies like _ga_MEASUREMENTID (e.g., G1.1.123456789.1678901234 where 1678901234 might be a session identifier)
  return "SESSION_ID_PLACEHOLDER";
};

const ContactFormWidget: React.FC<ContactFormWidgetProps> = ({
  formTitle = 'お問い合わせ',
  submitButtonText = '送信',
}) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [gaClientId, setGaClientId] = useState('');
  const [gaSessionId, setGaSessionId] = useState('');

  useEffect(() => {
    setGaClientId(getGAClientId());
    setGaSessionId(getGASessionId());
  }, []);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    // Actual submission logic will be added later.
    // This will involve sending data to apiEndpoint.
    console.log("Form submitted with data:", {
      name,
      email,
      message,
      ga_client_id: gaClientId,
      ga_session_id: gaSessionId,
    });
    // alert("Form submitted (see console for data). Actual API call not implemented yet.");
  };

  const styles = {
    container: {
      border: '1px solid #ccc',
      padding: '20px',
      borderRadius: '8px',
      backgroundColor: '#f9f9f9',
      maxWidth: '500px',
      fontFamily: 'Arial, sans-serif',
    },
    heading: {
      textAlign: 'center' as 'center',
      color: '#333',
      marginBottom: '20px',
    },
    formGroup: {
      marginBottom: '15px',
    },
    label: {
      display: 'block',
      marginBottom: '5px',
      color: '#555',
      fontSize: '14px',
    },
    input: {
      width: 'calc(100% - 20px)',
      padding: '10px',
      border: '1px solid #ddd',
      borderRadius: '4px',
      fontSize: '16px',
    },
    textarea: {
      width: 'calc(100% - 20px)',
      padding: '10px',
      border: '1px solid #ddd',
      borderRadius: '4px',
      fontSize: '16px',
      minHeight: '80px',
      resize: 'vertical' as 'vertical',
    },
    button: {
      width: '100%',
      padding: '10px 15px',
      backgroundColor: '#007bff',
      color: 'white',
      border: 'none',
      borderRadius: '4px',
      fontSize: '16px',
      cursor: 'pointer',
      transition: 'background-color 0.2s ease-in-out',
    },
    // buttonHover: { // Note: Inline styles don't directly support pseudo-classes like :hover
    //   backgroundColor: '#0056b3',
    // }
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.heading}>{formTitle}</h2>
      <form onSubmit={handleSubmit}>
        <div style={styles.formGroup}>
          <label htmlFor="contact-name" style={styles.label}>Name</label>
          <input
            type="text"
            id="contact-name"
            name="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            style={styles.input}
          />
        </div>

        <div style={styles.formGroup}>
          <label htmlFor="contact-email" style={styles.label}>Email</label>
          <input
            type="email"
            id="contact-email"
            name="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={styles.input}
          />
        </div>

        <div style={styles.formGroup}>
          <label htmlFor="contact-message" style={styles.label}>Message</label>
          <textarea
            id="contact-message"
            name="message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            required
            style={styles.textarea}
          />
        </div>

        <input type="hidden" name="ga_client_id" value={gaClientId} />
        <input type="hidden" name="ga_session_id" value={gaSessionId} />

        <button type="submit" style={styles.button}>
          {submitButtonText}
        </button>
      </form>
    </div>
  );
};

export default ContactFormWidget;
