"use strict";

const SPARK_COUNT = 40;

function launchSparks(count) {
  for (let i = 0; i < count; i += 1) {
    const spark = document.createElement("span");
    const size = 4 + Math.random() * 8;
    spark.className = "spark";
    spark.style.width = `${size}px`;
    spark.style.height = `${size}px`;
    spark.style.left = `${Math.random() * 100}vw`;
    spark.style.animationDuration = `${2 + Math.random() * 3}s`;
    spark.addEventListener("animationend", () => spark.remove());
    document.body.appendChild(spark);
  }
}

document.getElementById("sparkle-btn").addEventListener("click", () => {
  launchSparks(SPARK_COUNT);
});

launchSparks(SPARK_COUNT);
