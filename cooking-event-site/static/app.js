const form = document.querySelector(".registration-form");

if (form) {
    const countryDetails = JSON.parse(form.dataset.countryDetails);
    const countryField = document.getElementById("country");
    const dishField = document.getElementById("dish");
    const dishList = document.getElementById("dish-list");
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

    countryImage.addEventListener("load", () => {
        countryPreview.classList.add("has-image");
        countryPreviewMedia.setAttribute("aria-hidden", "false");
    });

    countryImage.addEventListener("error", () => {
        hidePreviewImage();
        previewCopy.textContent = "Image preview unavailable right now, but the team board and dish list still work.";
    });

    const setDishOptions = (country) => {
        const dishes = country ? countryDetails[country].dishes : [];
        dishField.innerHTML = "";

        if (!country) {
            dishField.disabled = true;
            dishField.innerHTML = '<option value="">Select a country first</option>';
            return;
        }

        dishField.disabled = false;
        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Choose your dish";
        dishField.appendChild(placeholder);

        dishes.forEach((dish) => {
            const option = document.createElement("option");
            option.value = dish;
            option.textContent = dish;
            dishField.appendChild(option);
        });
    };

    const renderDishList = (country) => {
        const dishes = country ? countryDetails[country].dishes : [];
        dishList.innerHTML = "";

        if (!country) {
            dishList.classList.add("empty-state");
            dishList.innerHTML = "<li>Select a country to reveal its dish shortlist.</li>";
            return;
        }

        dishList.classList.remove("empty-state");
        dishes.forEach((dish) => {
            const item = document.createElement("li");
            item.textContent = dish;
            dishList.appendChild(item);
        });
    };

    const renderPreview = (country) => {
        if (!country) {
            countryPreview.classList.add("empty-state");
            hidePreviewImage();
            countrySpotlight.textContent = "Featured Dish";
            previewTitle.textContent = "Pick a country to preview the team style";
            previewCopy.textContent = "You will see the flag, featured dish, and who has already joined.";
            return;
        }

        const details = countryDetails[country];
        countryPreview.classList.remove("empty-state");
        hidePreviewImage();
        countryImage.src = details.image_url;
        countryImage.alt = details.image_alt;
        countrySpotlight.textContent = `${details.flag} Featured Dish`;
        previewTitle.textContent = `${country} spotlight: ${details.spotlight}`;
        previewCopy.textContent = "Choose this country to join the shared team board and coordinate dishes together.";
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
        boardTitle.textContent = `${data.flag} ${country} team board`;

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
        const flag = country ? countryDetails[country].flag : "";
        boardTitle.textContent = country ? `${flag} ${country} team board` : "Choose a country to see dishes and teammates";
        setDishOptions(country);
        renderDishList(country);
        renderPreview(country);
        await renderMembers(country);
    });
}
