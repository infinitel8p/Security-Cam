import Navitem from "./Navitem";

const Navbar = () => {
    return (
        <div className="p-6 bg-zinc-950 text-white lg:h-screen lg:fixed lg:w-40 lg:l-0 lg:flex flex-col items-center justify-between">
            <p>Security-Cam Dashboard</p>
            <nav>
                <ul className="flex flex-col gap-y-10">
                    <Navitem title="Home" slug="/" />
                    <Navitem title="Archive" slug="/archive" />
                    <Navitem title="Settings" slug="/settings" />
                </ul>
            </nav>
            <div>
                <ul>
                    <Navitem title="Github" slug="https://github.com/infinitel8p/Security-Cam" />
                </ul>
            </div>
        </div>
    );
};

export default Navbar;
