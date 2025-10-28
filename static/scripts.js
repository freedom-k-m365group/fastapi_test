/* static/scripts.js */
$(document).ready(function () {
  // Socket.IO setup
  const socket = io.connect(window.location.origin, { path: "/socket.io/" });

  socket.on("connect", function () {
    console.log("Connected to Socket.IO");
  });

  socket.on("comic_generated", function (data) {
    $("#comic-status").text("Comic generated! ID: " + data.comic_id);
    loadComics();
  });

  socket.on("comic_error", function (data) {
    $("#comic-status").text("Error generating comic: " + data.error);
  });

  // Load heroes
  function loadHeroes() {
    $.get("/heroes/", function (data) {
      $("#heroes-list").empty();
      data.forEach((hero) => {
        $("#heroes-list").append(`<li>${hero.hero_name} (ID: ${hero.id})</li>`);
      });
      // Populate select for comics
      $("#hero-ids").empty();
      data.forEach((hero) => {
        $("#hero-ids").append(
          `<option value="${hero.id}">${hero.hero_name}</option>`
        );
      });
    });
  }

  // Load villains
  function loadVillains() {
    $.get("/villians/", function (data) {
      $("#villains-list").empty();
      data.forEach((villain) => {
        $("#villains-list").append(
          `<li>${villain.villian_name} (ID: ${villain.id})</li>`
        );
      });
      // Populate select for comics
      $("#villian-ids").empty();
      data.forEach((villain) => {
        $("#villian-ids").append(
          `<option value="${villain.id}">${villain.villian_name}</option>`
        );
      });
    });
  }

  // Load comics
  function loadComics() {
    $.get("/comics/", function (data) {
      $("#comics-list").empty();
      data.forEach((comic) => {
        $("#comics-list").append(
          `<li>Comic ID: ${comic.id} - Summary: ${comic.summary.substring(
            0,
            100
          )}...</li>`
        );
      });
    });
  }

  // Create hero
  $("#create-hero-form").submit(function (e) {
    e.preventDefault();
    $.post("/heroes/", { hero_name: $("#hero-name").val() }, function (data) {
      $("#hero-status").text("Hero created: " + data.hero_name);
      loadHeroes();
    });
  });

  // Create villain
  $("#create-villain-form").submit(function (e) {
    e.preventDefault();
    $.post(
      "/villians/",
      { hero_name: $("#villain-name").val() },
      function (data) {
        $("#villain-status").text("Villain created: " + data.villian_name);
        loadVillains();
      }
    );
  });

  // Create comic
  $("#create-comic-form").submit(function (e) {
    e.preventDefault();
    const heroIds = $("#hero-ids").val() || [];
    const villianIds = $("#villian-ids").val() || [];
    $.ajax({
      url: "/comics/",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({
        hero_ids: heroIds.map(Number),
        villian_ids: villianIds.map(Number),
      }),
      success: function (data) {
        $("#comic-status").text("Task queued: " + data.task_id);
        socket.emit("join_task", { task_id: data.task_id });
      },
    });
  });

  // Initial loads
  loadHeroes();
  loadVillains();
  loadComics();
});
