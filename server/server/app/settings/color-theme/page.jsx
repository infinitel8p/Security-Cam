"use client";
import ThemeTile from "@/components/ThemeTile";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

const themeData = [{ name: "lightPurple" }, { name: "darkPurple" }];

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
				{themeData.map((childTheme) => (
					<ThemeTile
						key={childTheme.name}
						name={childTheme.name}
						activeTheme={theme}
						handleClick={handleTheme}
					/>
				))}
			</div>
		</>
	);
}

export default ColorTheme;
