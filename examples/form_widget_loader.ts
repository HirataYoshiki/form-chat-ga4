(() => {
  const scriptElement = document.currentScript as HTMLScriptElement | null;

  if (!scriptElement) {
    console.error("Error: Could not find the script element. Make sure this script is not loaded as a module or asynchronously without `async=false`.");
    return;
  }

  const formId = scriptElement.getAttribute("data-form-id");
  const apiEndpoint = scriptElement.getAttribute("data-api-endpoint") || 'https://api.example.com/submit';
  const theme = scriptElement.getAttribute("data-theme") || 'light';
  const position = scriptElement.getAttribute("data-position") || 'bottom-right';
  const title = scriptElement.getAttribute("data-title") || 'お問い合わせ';
  const buttonText = scriptElement.getAttribute("data-button-text") || '送信';

  if (!formId) {
    console.error("Error: data-form-id attribute is required and was not found on the script tag.");
    return;
  }

  console.log("Contact Form Widget Loader: Attributes collected:");
  console.log("  Form ID:        ", formId);
  console.log("  API Endpoint:   ", apiEndpoint);
  console.log("  Theme:          ", theme);
  console.log("  Position:       ", position);
  console.log("  Title:          ", title);
  console.log("  Button Text:    ", buttonText);

  const placeholderDiv = document.createElement('div');
  placeholderDiv.id = `contact-form-widget-placeholder-${formId}`;
  placeholderDiv.textContent = `Contact form widget (form-id: ${formId}) will be loaded here. Position: ${position}, Theme: ${theme}, Title: "${title}", Button: "${buttonText}", API: "${apiEndpoint}"`;
  placeholderDiv.style.cssText = `
    padding: 20px;
    margin: 10px 0;
    border: 1px dashed #ccc;
    background-color: #f9f9f9;
    text-align: center;
    font-family: sans-serif;
  `;
  document.body.appendChild(placeholderDiv);

})();
