document.addEventListener("DOMContentLoaded", function () {
  // ==========================================
  // 1. PROGRESS BAR TARGET TABUNGAN
  // ==========================================
  const progressBars = document.querySelectorAll("[data-progress]");

  progressBars.forEach(function (bar) {
    const progress = Number(bar.dataset.progress);

    if (Number.isFinite(progress)) {
      const safeProgress = Math.min(Math.max(progress, 0), 100);

      bar.style.width = safeProgress + "%";
    }
  });

  // ==========================================
  // 2. KONFIRMASI HAPUS DATA
  // ==========================================
  const deleteForms = document.querySelectorAll("form[data-confirm-delete]");

  deleteForms.forEach(function (form) {
    form.addEventListener("submit", function (event) {
      const message =
        form.dataset.confirmDelete || "Yakin ingin menghapus data ini?";

      if (!window.confirm(message)) {
        event.preventDefault();
      }
    });
  });

  // ==========================================
  // 3. VALIDASI INPUT ANGKA
  // ==========================================
  const numberInputs = document.querySelectorAll('input[type="number"]');

  numberInputs.forEach(function (input) {
    input.addEventListener("input", function () {
      if (input.value !== "" && Number(input.value) < 0) {
        input.setCustomValidity("Jumlah tidak boleh negatif.");
      } else {
        input.setCustomValidity("");
      }
    });
  });

  // ==========================================
  // 4. KONFIRMASI TOMBOL HAPUS LAINNYA
  // ==========================================
  const deleteButtons = document.querySelectorAll(".delete-button");

  deleteButtons.forEach(function (button) {
    button.addEventListener("click", function (event) {
      const form = button.closest("form");

      if (!form || form.hasAttribute("data-confirm-delete")) {
        return;
      }

      const inlineConfirmation = form.getAttribute("onsubmit");

      // Jangan menampilkan konfirmasi dua kali.
      if (inlineConfirmation) {
        return;
      }

      const confirmed = window.confirm("Yakin ingin menghapus data ini?");

      if (!confirmed) {
        event.preventDefault();
      }
    });
  });

  // ==========================================
  // 5. EFEK FOKUS PADA INPUT FORM
  // ==========================================
  const formInputs = document.querySelectorAll(
    ".transaction-form input, " +
      ".transaction-form select, " +
      ".savings-add-form input",
  );

  formInputs.forEach(function (input) {
    input.addEventListener("focus", function () {
      input.classList.add("input-focused");
    });

    input.addEventListener("blur", function () {
      input.classList.remove("input-focused");
    });
  });

  // ==========================================
  // 6. CEGAH SUBMIT BERULANG KALI
  // ==========================================
  const forms = document.querySelectorAll(
    ".transaction-form, .savings-add-form",
  );

  forms.forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        form.reportValidity();
        return;
      }

      const submitButton = form.querySelector('button[type="submit"]');

      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = "Memproses...";
      }
    });
  });
});
