/* ============================================================
   Boomi Labs — Google Analytics (GA4)
   ------------------------------------------------------------
   Shared loader referenced from every page's <head>. The
   Measurement ID lives ONLY here — update it in one place.
   Loaded as a normal (non-async) script so window.gtag is
   defined before lab.js runs and can fire per-step events;
   the heavy gtag.js loader below is injected asynchronously,
   so page rendering is never blocked.
   ============================================================ */
(function () {
  'use strict';
  var GA_ID = 'G-1WEVGRJD9Q';

  // Inject the official gtag.js loader asynchronously (non-blocking).
  var loader = document.createElement('script');
  loader.async = true;
  loader.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
  document.head.appendChild(loader);

  // Standard gtag bootstrap — defined synchronously so other scripts can use it.
  window.dataLayer = window.dataLayer || [];
  window.gtag = function () { window.dataLayer.push(arguments); };
  window.gtag('js', new Date());
  window.gtag('config', GA_ID);

  // Exposed so lab.js (and future scripts) can reference the active ID.
  window.BOOMI_GA_ID = GA_ID;
}());
