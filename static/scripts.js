/* static/scripts.js */
$(document).ready(function () {
  // Socket.IO setup
  const socket = io.connect(window.location.origin, { path: "/socket.io/" });

  socket.on("connect", function () {
    console.log("Connected to Socket.IO");
  });

  let pending_comic_id = null;

  socket.on("comic_generated", function (data) {
    $("#comic-banner").hide();
    alert("Comic summary has been generated! ID: " + data.comic_id);
    pending_comic_id = data.comic_id;
    loadComics();
  });

  socket.on("comic_error", function (data) {
    $("#comic-banner").hide();
    $("#comic-status").text("Error generating comic: " + data.error);
  });

  // Event delegation for expandable items
  $(document).on("click", ".expandable .header", function () {
    var $li = $(this).closest(".expandable");
    $(".expandable.expanded").not($li).removeClass("expanded");
    $li.toggleClass("expanded");
  });

  // Load heroes
  function loadHeroes() {
    $("#heroes-loader").show();
    $("#heroes-list").hide();
    $.get("/heroes/", function (data) {
      $("#heroes-list").empty();
      data.forEach((hero) => {
        let content = `
          <p>Real Name: ${hero.real_name || "N/A"}</p>
          <p>Age: ${hero.age || "N/A"}</p>
          <p>Origin: ${hero.origin || "N/A"}</p>
          <p>Height (cm): ${hero.height_cm || "N/A"}</p>
          <p>Weight (kg): ${hero.weight_kg || "N/A"}</p>
          <p>Eye Color: ${hero.eye_color || "N/A"}</p>
          <p>Hair Color: ${hero.hair_color || "N/A"}</p>
          <p>Powers: ${hero.powers || "N/A"}</p>
          <p>Strength Level: ${hero.strength_level || "N/A"}</p>
          <p>Speed Level: ${hero.speed_level || "N/A"}</p>
          <p>Durability Level: ${hero.durability_level || "N/A"}</p>
          <p>Intelligence Level: ${hero.intelligence_level || "N/A"}</p>
          <p>Weaknesses: ${hero.weaknesses || "N/A"}</p>
          <p>Strengths: ${hero.strengths || "N/A"}</p>
          <p>Description: ${hero.description || "N/A"}</p>
        `;
        $("#heroes-list").append(`
          <li class="expandable" data-id="${hero.id}">
            <div class="header">${hero.hero_name} (ID: ${hero.id})</div>
            <div class="content">${content}</div>
          </li>
        `);
      });
      // Populate select for comics
      $("#hero-ids").empty();
      data.forEach((hero) => {
        $("#hero-ids").append(
          `<option value="${hero.id}">${hero.hero_name}</option>`
        );
      });
      $("#heroes-loader").hide();
      $("#heroes-list").show();
    }).fail(function () {
      $("#heroes-loader").hide();
      $("#hero-status").text("Error loading heroes.");
    });
  }

  // Load villains
  function loadVillains() {
    $("#villains-loader").show();
    $("#villains-list").hide();
    $.get("/villains/", function (data) {
      // ← Fixed: was /villians/
      $("#villains-list").empty();
      data.forEach((villain) => {
        let content = `
                <p>Real Name: ${villain.real_name || "N/A"}</p>
                <p>Age: ${villain.age || "N/A"}</p>
                <p>Origin: ${villain.origin || "N/A"}</p>
                <p>Height (cm): ${villain.height_cm || "N/A"}</p>
                <p>Weight (kg): ${villain.weight_kg || "N/A"}</p>
                <p>Eye Color: ${villain.eye_color || "N/A"}</p>
                <p>Hair Color: ${villain.hair_color || "N/A"}</p>
                <p>Powers: ${villain.powers || "N/A"}</p>
                <p>Strength Level: ${villain.strength_level || "N/A"}</p>
                <p>Speed Level: ${villain.speed_level || "N/A"}</p>
                <p>Durability Level: ${villain.durability_level || "N/A"}</p>
                <p>Intelligence Level: ${
                  villain.intelligence_level || "N/A"
                }</p>
                <p>Weaknesses: ${villain.weaknesses || "N/A"}</p>
                <p>Strengths: ${villain.strengths || "N/A"}</p>
                <p>Description: ${villain.description || "N/A"}</p>
            `;
        $("#villains-list").append(`
                <li class="expandable" data-id="${villain.id}">
                    <div class="header">${villain.villain_name} (ID: ${villain.id})</div>
                    <div class="content">${content}</div>
                </li>
            `);
      });
      // Populate select for comics
      $("#villain-ids").empty();
      data.forEach((villain) => {
        $("#villain-ids").append(
          `<option value="${villain.id}">${villain.villain_name}</option>`
        );
      });
      $("#villains-loader").hide();
      $("#villains-list").show();
    }).fail(function () {
      $("#villains-loader").hide();
      $("#villain-status").text("Error loading villains.");
    });
  }

  // Load comics
  function loadComics() {
    $("#comics-loader").show();
    $("#comics-list").hide();
    $.get("/comics/", function (data) {
      $("#comics-list").empty();
      data.forEach((comic) => {
        let shortSummary = comic.summary.substring(0, 100) + "...";
        let fullSummary = comic.summary.replace(/\n/g, "<br>");
        $("#comics-list").append(`
          <li class="expandable" data-id="${comic.id}">
            <div class="header">Comic ID: ${comic.id} - Summary: ${shortSummary}</div>
            <div class="content">${fullSummary}</div>
          </li>
        `);
      });
      $("#comics-loader").hide();
      $("#comics-list").show();
      if (pending_comic_id) {
        var $li = $('#comics-list li[data-id="' + pending_comic_id + '"]');
        $(".expandable.expanded").removeClass("expanded");
        $li.addClass("expanded");
        pending_comic_id = null;
      }
    }).fail(function () {
      $("#comics-loader").hide();
      $("#comic-status").text("Error loading comics.");
    });
  }

  // Create hero
  $("#create-hero-form").submit(function (e) {
    e.preventDefault();
    $("#hero-status").text("Creating hero...");
    $("#heroes-loader").show();
    $("#heroes-list").hide();
    $.ajax({
      url: "/heroes/",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({ hero_name: $("#hero-name").val() }),
      success: function (data) {
        $("#hero-status").text("Hero created: " + data.hero_name);
        loadHeroes();
      },
      error: function (xhr) {
        $("#heroes-loader").hide();
        $("#heroes-list").show();
        $("#hero-status").text(
          "Error creating hero: " +
            (xhr.responseJSON?.detail || "Unknown error")
        );
      },
    });
  });

  // Create villain (update similarly, but see Fix 2 for field name change)
  $("#create-villain-form").submit(function (e) {
    e.preventDefault();
    $("#villain-status").text("Creating villain...");
    $("#villains-loader").show();
    $("#villains-list").hide();
    $.ajax({
      url: "/villains/",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({ hero_name: $("#villain-name").val() }), // Change to villain_name after Fix 2
      success: function (data) {
        $("#villain-status").text("Villain created: " + data.villain_name);
        loadVillains();
      },
      error: function (xhr) {
        $("#villains-loader").hide();
        $("#villains-list").show();
        $("#villain-status").text(
          "Error creating villain: " +
            (xhr.responseJSON?.detail || "Unknown error")
        );
      },
    });
  });

  // Create comic
  $("#create-comic-form").submit(function (e) {
    e.preventDefault();
    const heroIds = $("#hero-ids").val() || [];
    const villainIds = $("#villain-ids").val() || [];
    $("#comic-banner").show();
    $("#comic-status").text("");
    $.ajax({
      url: "/comics/",
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify({
        hero_ids: heroIds.map(Number),
        villain_ids: villainIds.map(Number),
      }),
      success: function (data) {
        socket.emit("join_task", { task_id: data.task_id });
      },
      error: function () {
        $("#comic-banner").hide();
        $("#comic-status").text("Error queuing comic generation.");
      },
    });
  });

  // Initial loads
  loadHeroes();
  loadVillains();
  loadComics();
});
