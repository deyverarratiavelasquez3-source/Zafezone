// login.js
// Muestra u oculta la contraseña al hacer clic en el "ojito".
// Funciona en el login y en el registro (cambia todos los campos
// de contraseña que tengan el atributo data-password).

const boton = document.getElementById("togglePassword");
const icono = document.getElementById("iconoVista");
const camposPassword = document.querySelectorAll("input[data-password]");

boton.addEventListener("click", function () {
    // ¿Ahora mismo la contraseña está oculta?
    const estaOculta = camposPassword[0].type === "password";

    // Si estaba oculta la mostramos, y al revés
    camposPassword.forEach(function (campo) {
        campo.type = estaOculta ? "text" : "password";
    });

    // Cambiamos el icono y los textos de accesibilidad
    icono.src = estaOculta ? boton.dataset.iconoOcultar : boton.dataset.iconoVer;
    boton.setAttribute("aria-label", estaOculta ? "Ocultar contraseña" : "Mostrar contraseña");
    boton.setAttribute("aria-pressed", estaOculta ? "true" : "false");
});
