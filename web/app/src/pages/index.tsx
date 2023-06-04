import Main from "@/components/main";
import Head from "next/head";
import { RecoilRoot } from "recoil";

export default function Home() {
  return (
    <>
      <Head>
        <title>Router Lab</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <RecoilRoot>
        <Main />
      </RecoilRoot>
    </>
  );
}
