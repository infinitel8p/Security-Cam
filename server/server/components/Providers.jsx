"use client";
import { ThemeProvider } from "next-themes";
import SideBar from "@/components/SideBar";
import StatusBar from "./StatusBar";

function Providers({ children }) {
	return (
		<ThemeProvider defaultTheme="darkPurple">
			<SideBar />
			<div className="pt-[5rem] pl-10 pr-10 lg:pt-5 lg:pl-[20rem] h-[100vh] bg-[var(--color-primary)] text-[var(--color-text)]">
				{children}
			</div>
		</ThemeProvider>
	);
}

export default Providers;
