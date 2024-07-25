import Link from "next/link";

interface Props {
    title: string;
    slug: string;
}

const Navitem = ({ title, slug }: Props) => {
    return (
        <li>
            <Link href={slug} className="w-full hover:bg-blue-500 bg-amber-50 py-2 px-4 border border-blue-500 hover:border-red-500 rounded-md text-zinc-950">
                {title}
            </Link>
        </li>
    )
}

export default Navitem