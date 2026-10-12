/* Prototipo navegable — interacción mínima para simular el flujo de voto.
   No guarda datos: solo pasa la opción elegida entre pantallas por la URL. */
(function () {
  "use strict";

  var params = new URLSearchParams(window.location.search);

  // UI-07 Opciones disponibles: habilita "Continuar" y lleva la opción elegida
  var formOpciones = document.getElementById("form-opciones");
  if (formOpciones) {
    var continuar = document.getElementById("btn-continuar");
    var aviso = document.getElementById("aviso-seleccion");
    formOpciones.addEventListener("change", function (e) {
      if (e.target.name !== "opcion") return;
      continuar.classList.remove("disabled");
      continuar.removeAttribute("aria-disabled");
      continuar.href = "confirmar.html?opcion=" + encodeURIComponent(e.target.value);
      if (aviso) aviso.textContent = "Elegiste: " + e.target.value;
    });
  }

  // UI-08 y UI-09: muestran la opción que llegó por la URL
  var elegida = params.get("opcion");
  document.querySelectorAll("[data-opcion-elegida]").forEach(function (el) {
    if (elegida) el.textContent = elegida;
  });
  var confirmar = document.getElementById("btn-confirmar");
  if (confirmar && elegida) {
    confirmar.href = "voto-registrado.html?opcion=" + encodeURIComponent(elegida);
  }

  // Formularios de demostración: no envían nada, solo avisan
  document.querySelectorAll("form[data-demo]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var destino = form.getAttribute("data-destino");
      if (destino) { window.location.href = destino; return; }
      var msg = form.querySelector("[data-mensaje]");
      if (msg) {
        msg.hidden = false;
        msg.focus();
      }
    });
  });
})();

/* UI-01 Inicio: cuenta regresiva hasta el Festival 2027 (28 de abril, hora de Colombia) */
(function () {
  "use strict";
  var caja = document.getElementById("cuenta-regresiva");
  if (!caja) return;
  var objetivo = new Date(caja.getAttribute("data-fecha")).getTime();
  var campos = {};
  caja.querySelectorAll("[data-unidad]").forEach(function (el) {
    campos[el.getAttribute("data-unidad")] = el;
  });
  function dosDigitos(n) { return n < 10 ? "0" + n : String(n); }
  function actualizar() {
    var resta = Math.max(0, objetivo - Date.now());
    var s = Math.floor(resta / 1000);
    campos.dias.textContent = Math.floor(s / 86400);
    campos.horas.textContent = dosDigitos(Math.floor((s % 86400) / 3600));
    campos.minutos.textContent = dosDigitos(Math.floor((s % 3600) / 60));
    campos.segundos.textContent = dosDigitos(s % 60);
  }
  actualizar();
  setInterval(actualizar, 1000);
})();
