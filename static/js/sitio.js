/* Cuenta regresiva hasta la fecha de inicio de la edición activa.
   La fecha llega desde la base de datos en el atributo data-fecha (no está escrita en el código). */
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
