const form = document.querySelector(".registration-form");

if (form) {
    const countryDetails = JSON.parse(form.dataset.countryDetails);
    const countryField = document.getElementById("country");
    const dishField = document.getElementById("dish");
    const dishPicker = document.getElementById("dish-picker");
    const dishError = document.getElementById("dish-error");
    const memberList = document.getElementById("member-list");
    const boardTitle = document.getElementById("board-title");
    const countryImage = document.getElementById("country-image");
    const previewTitle = document.getElementById("preview-title");
    const previewCopy = document.getElementById("preview-copy");
    const countrySpotlight = document.getElementById("country-spotlight");
    const countryPreview = document.getElementById("country-preview");
    const countryPreviewMedia = document.getElementById("country-preview-media");

    const hidePreviewImage = () => {
        countryPreview.classList.remove("has-image");
        countryPreviewMedia.setAttribute("aria-hidden", "true");
        countryImage.removeAttribute("src");
        countryImage.alt = "";
    };

    const clearDishError = () => {
        dishError.hidden = true;
    };

    countryImage.addEventListener("load", () => {
        countryPreview.classList.add("has-image");
        countryPreviewMedia.setAttribute("aria-hidden", "false");
    });

    countryImage.addEventListener("error", () => {
        hidePreviewImage();
        previewCopy.textContent = "Image preview unavailable right now, but the cookout group board and dish list still work.";
    });

    const selectDish = (dishName) => {
        dishField.value = dishName;
        clearDishError();
        dishPicker.querySelectorAll(".dish-card").forEach((card) => {
            card.classList.toggle("is-selected", card.dataset.dishName === dishName);
            card.setAttribute(
                "aria-pressed",
                String(card.dataset.dishName === dishName)
            );
        });
    };

    const renderDishPicker = (country) => {
        const dishes = country ? countryDetails[country].dishes : [];
        dishField.value = "";
        dishPicker.innerHTML = "";

        if (!country) {
            dishPicker.classList.add("empty-state");
            dishPicker.innerHTML = '<p class="dish-picker-empty">Select a country first to load the dish choices.</p>';
            return;
        }

        dishPicker.classList.remove("empty-state");
        dishes.forEach((dish) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "dish-card";
            button.dataset.dishName = dish.name;
            button.setAttribute("aria-pressed", "false");

            const image = document.createElement("img");
            image.src = dish.image_url;
            image.alt = dish.image_alt;
            image.loading = "lazy";
            image.className = "dish-card-image";
            image.dataset.fallbackUrl = dish.fallback_image_url || "";
            image.dataset.fallbackAlt = dish.fallback_image_alt || "";
            image.addEventListener("load", () => {
                image.classList.remove("is-hidden");
                button.classList.remove("no-image");
            });
            image.addEventListener("error", () => {
                if (image.dataset.fallbackUrl && image.src !== image.dataset.fallbackUrl) {
                    image.src = image.dataset.fallbackUrl;
                    image.alt = image.dataset.fallbackAlt || `${country} featured dish`;
                    return;
                }
                image.classList.add("is-hidden");
                button.classList.add("no-image");
            });

            const labelWrap = document.createElement("div");
            labelWrap.className = "dish-card-copy";

            const title = document.createElement("strong");
            title.textContent = dish.name;

            const meta = document.createElement("span");
            meta.textContent = `${country} team option`;

            labelWrap.appendChild(title);
            labelWrap.appendChild(meta);
            button.appendChild(image);
            button.appendChild(labelWrap);
            button.addEventListener("click", () => selectDish(dish.name));
            dishPicker.appendChild(button);
        });
    };

    const renderPreview = (country) => {
        if (!country) {
            countryPreview.classList.add("empty-state");
            hidePreviewImage();
            countrySpotlight.textContent = "Featured Dish";
            previewTitle.textContent = "Pick a country to preview the cookout group";
            previewCopy.textContent = "You will see the flag, featured dish, and who has already joined that country group.";
            return;
        }

        const details = countryDetails[country];
        countryPreview.classList.remove("empty-state");
        hidePreviewImage();
        countryImage.src = details.image_url;
        countryImage.alt = details.image_alt;
        countrySpotlight.textContent = "Featured Dish";
        previewTitle.textContent = `${country} spotlight: ${details.spotlight}`;
        previewCopy.textContent = "Choose this country to join the shared group board and coordinate dishes together for the cookout.";
    };

    const renderMembers = async (country) => {
        memberList.innerHTML = "";

        if (!country) {
            memberList.classList.add("empty-state");
            memberList.innerHTML = "<li>No country selected yet.</li>";
            return;
        }

        let response;
        try {
            response = await fetch(`/api/countries/${encodeURIComponent(country)}/members`);
        } catch (_error) {
            memberList.classList.add("empty-state");
            memberList.innerHTML = "<li>Unable to load teammates right now.</li>";
            return;
        }
        if (!response.ok) {
            memberList.classList.add("empty-state");
            memberList.innerHTML = "<li>Unable to load teammates right now.</li>";
            return;
        }

        const data = await response.json();
        boardTitle.textContent = `${country} team board`;

        if (!data.members.length) {
            memberList.classList.add("empty-state");
            memberList.innerHTML = "<li>No one has joined this country yet.</li>";
            return;
        }

        memberList.classList.remove("empty-state");
        data.members.forEach((member) => {
            const item = document.createElement("li");
            const name = document.createElement("strong");
            name.textContent = member.name;

            const lineBreak = document.createElement("br");

            const dish = document.createElement("span");
            dish.textContent = member.dish;

            item.appendChild(name);
            item.appendChild(lineBreak);
            item.appendChild(dish);
            memberList.appendChild(item);
        });
    };

    countryField.addEventListener("change", async (event) => {
        const country = event.target.value;
        boardTitle.textContent = country ? `${country} team board` : "Choose a country to see dishes and teammates";
        clearDishError();
        renderDishPicker(country);
        renderPreview(country);
        await renderMembers(country);
    });

    form.addEventListener("submit", (event) => {
        if (!dishField.value) {
            event.preventDefault();
            dishError.hidden = false;
            dishPicker.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    });
}
