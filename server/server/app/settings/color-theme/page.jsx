"use client";
import ThemeTile from "@/components/ThemeTile";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

const themes = [{ name: "lightPurple" }, { name: "darkPurple" }];

function ColorTheme() {
	const [mounted, setMounted] = useState(false);
	const { theme, setTheme } = useTheme();

	useEffect(() => setMounted(true), []);

	if (!mounted) return null;

	const handleTheme = (name) => {
		setTheme(name);
	};

	return (
		<>
			<h1 className="font-bold text-2xl mb-5">Choose your Color Theme:</h1>
			<h2 className="font-semibold text-lg mb-3">Current theme: {mounted && theme}</h2>
			<div className="flex flex-col gap-3">
				{themes.map((theme) => (
					<ThemeTile key={theme.name} name={theme.name} handleClick={handleTheme} />
				))}
			</div>
		</>
	);
}

export default ColorTheme;
