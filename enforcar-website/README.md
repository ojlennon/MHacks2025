# EnforcAR Website

A modern, responsive website for EnforcAR - an AR-powered license plate scanning solution for law enforcement using Snap Spectacles.

## Features

- **Modern Design**: Clean black and orange theme with professional aesthetics
- **Responsive Layout**: Fully responsive design that works on all devices
- **Interactive Components**: 
  - Animated AR demo visualization
  - Interactive FAQ section
  - Contact form with validation
  - Smooth scrolling navigation
  - Hover effects and animations
- **Performance Optimized**: Fast loading with optimized assets and code
- **Accessibility**: Keyboard navigation and screen reader friendly

## Pages

1. **Homepage**: Hero section with clear value proposition and AR demo
2. **About**: Problem/solution explanation with statistics
3. **Features**: Six key features with icons and descriptions
4. **Use Cases**: Four main use cases for law enforcement
5. **Demo**: Step-by-step how-it-works guide
6. **FAQ**: Common questions with expandable answers
7. **Contact**: Contact form and company information

## Technology Stack

- **HTML5**: Semantic markup
- **CSS3**: Modern styling with CSS Grid, Flexbox, and animations
- **JavaScript (ES6+)**: Interactive functionality and animations
- **Font Awesome**: Icons
- **Google Fonts**: Inter font family

## File Structure

```
enforcar-website/
├── index.html              # Main HTML file
├── assets/
│   ├── css/
│   │   └── style.css       # Main stylesheet
│   ├── js/
│   │   └── script.js       # JavaScript functionality
│   └── images/             # Image assets (placeholder)
├── pages/                  # Additional pages (if needed)
└── README.md              # This file
```

## Getting Started

1. Clone or download the project
2. Open `index.html` in a web browser
3. No build process required - it's a static website

## Customization

### Colors
The color scheme can be customized by modifying CSS variables in `style.css`:

```css
:root {
    --primary-color: #ff6b35;    /* Orange */
    --secondary-color: #1a1a1a;  /* Dark gray */
    --accent-color: #ff6b35;     /* Orange accent */
    --text-primary: #ffffff;     /* White text */
    --text-secondary: #b0b0b0;   /* Light gray text */
}
```

### Content
- Update text content directly in `index.html`
- Modify contact information in the contact section
- Add/remove features in the features section
- Update FAQ questions and answers

### Images
- Add images to `assets/images/` directory
- Update image references in HTML
- Optimize images for web (WebP format recommended)

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- Optimized CSS and JavaScript
- Minimal external dependencies
- Responsive images
- Smooth animations with hardware acceleration
- Debounced scroll events for performance

## License

This project is created for EnforcAR and is proprietary software.

## Contact

For questions about this website, contact the development team.
