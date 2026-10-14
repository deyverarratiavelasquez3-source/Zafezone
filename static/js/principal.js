// principal.js
// Hace funcionar los botones de "Lugar" (denuncia) y de "Emoción" (diario).
// Los botones no envían nada por sí solos: al hacer clic marcamos el botón
// elegido y guardamos su valor en un campo oculto del formulario.

// ---------- Botones de lugar (Curso / Patio / Cafetería) ----------
const botonesLugar = document.querySelectorAll(".lugares button");
const campoLugar = document.getElementById("campo-lugar");

botonesLugar.forEach(function (boton) {
    boton.addEventListener("click", function () {
        // Quitamos la marca a todos y se la ponemos solo al que se pulsó
        botonesLugar.forEach(function (b) { b.classList.remove("seleccionado"); });
        boton.classList.add("seleccionado");

        // Guardamos el valor para que viaje con el formulario
        campoLugar.value = boton.dataset.lugar;
    });
});

// ---------- Botones de emoción (Feliz / Normal / Abrumado / Triste) ----------
const botonesEmocion = document.querySelectorAll(".emociones button");
const campoEmocion = document.getElementById("campo-emocion");

botonesEmocion.forEach(function (boton) {
    boton.addEventListener("click", function () {
        botonesEmocion.forEach(function (b) { b.classList.remove("elegida"); });
        boton.classList.add("elegida");

        campoEmocion.value = boton.dataset.emocion;
    });
});
