/**
 * Main entry point for Glide HUD
 */

import { WebSocketClient } from './ws-client.js';

class HUDController {
  constructor() {
    this.hudElement = document.getElementById('hud');
    this.arrowUp = document.querySelector('.arrow-up');
    this.arrowDown = document.querySelector('.arrow-down');
    this.speedBars = document.querySelectorAll('.speed-bar');
    
    // Get WebSocket token from URL params if present
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token') || undefined;
    
    this.wsClient = new WebSocketClient();
    this.setupEventHandlers();
    this.wsClient.connect(token);
  }
  
  setupEventHandlers() {
    // Handle scroll events
    this.wsClient.on('scroll', (event) => {
      this.showHUD();
      this.updateDirection(event.vy);
      this.updateSpeed(event.speed);
    });
    
    // Handle hide events
    this.wsClient.on('hide', () => {
      this.hideHUD();
    });
    
    // Handle config events
    this.wsClient.on('config', (event) => {
      this.updatePosition(event.position);
      this.updateOpacity(event.opacity);
    });
  }
  
  showHUD() {
    this.hudElement.classList.remove('hidden');
  }
  
  hideHUD() {
    this.hudElement.classList.add('hidden');
  }
  
  updateDirection(vy) {
    // Remove active from both arrows
    this.arrowUp.classList.remove('active');
    this.arrowDown.classList.remove('active');
    
    // Show appropriate arrow based on velocity
    if (vy < 0) {
      this.arrowUp.classList.add('active');
    } else if (vy > 0) {
      this.arrowDown.classList.add('active');
    }
  }
  
  updateSpeed(speed) {
    // Speed is 0-1, show proportional bars
    const activeBars = Math.ceil(speed * this.speedBars.length);
    
    this.speedBars.forEach((bar, index) => {
      if (index < activeBars) {
        bar.classList.add('active');
      } else {
        bar.classList.remove('active');
      }
    });
  }
  
  updatePosition(position) {
    // Reset position styles
    this.hudElement.style.removeProperty('top');
    this.hudElement.style.removeProperty('bottom');
    this.hudElement.style.removeProperty('left');
    this.hudElement.style.removeProperty('right');
    this.hudElement.style.removeProperty('transform');
    
    // Parse and apply position
    const [vertical, horizontal] = position.split('-');
    
    if (vertical === 'top') {
      this.hudElement.style.top = '40px';
    } else {
      this.hudElement.style.bottom = '40px';
    }
    
    if (horizontal === 'left') {
      this.hudElement.style.left = '40px';
    } else if (horizontal === 'right') {
      this.hudElement.style.right = '40px';
    } else if (horizontal === 'center') {
      this.hudElement.style.left = '50%';
      this.hudElement.style.transform = 'translateX(-50%)';
    }
  }
  
  updateOpacity(opacity) {
    this.hudElement.style.opacity = opacity;
  }
}

// Initialize HUD when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => new HUDController());
} else {
  new HUDController();
}